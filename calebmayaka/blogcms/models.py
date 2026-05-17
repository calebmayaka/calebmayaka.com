import math
import re
from django.db import models
from django.db.models import Count, Q
from django.utils import timezone
from modelcluster.fields import ParentalKey
from modelcluster.tags import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail import blocks
from wagtail.images import get_image_model_string
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Page
from wagtail.search import index


BLOG_RICH_TEXT_FEATURES = [
    'h2',
    'h3',
    'bold',
    'italic',
    'ol',
    'ul',
    'hr',
    'link',
    'document-link',
    'blockquote',
]


class BlogImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    alt_text = blocks.CharBlock(required=False, max_length=160)
    caption = blocks.CharBlock(required=False, max_length=220)

    class Meta:
        icon = 'image'
        label = 'Image'


class BlogCodeBlock(blocks.StructBlock):
    filename = blocks.CharBlock(required=False, max_length=120)
    language = blocks.ChoiceBlock(
        choices=[
            ('text', 'Plain text'),
            ('python', 'Python'),
            ('javascript', 'JavaScript'),
            ('typescript', 'TypeScript'),
            ('html', 'HTML'),
            ('css', 'CSS'),
            ('bash', 'Bash'),
            ('json', 'JSON'),
            ('sql', 'SQL'),
        ],
        default='python',
    )
    code = blocks.TextBlock()
    caption = blocks.CharBlock(required=False, max_length=220)

    class Meta:
        icon = 'code'
        label = 'Code snippet'


class BlogCalloutBlock(blocks.StructBlock):
    style = blocks.ChoiceBlock(
        choices=[
            ('note', 'Note'),
            ('tip', 'Tip'),
            ('warning', 'Warning'),
        ],
        default='note',
    )
    heading = blocks.CharBlock(required=False, max_length=120)
    text = blocks.RichTextBlock(features=BLOG_RICH_TEXT_FEATURES)

    class Meta:
        icon = 'info-circle'
        label = 'Callout'


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        posts = (
            BlogPostPage.objects.live()
            .public()
            .descendant_of(self)
            .select_related('cover_image', 'owner')
            .prefetch_related('tags')
            .order_by('-date', '-first_published_at')
        )
        featured_post = posts.filter(featured=True).first() or posts.first()

        context['featured_post'] = featured_post
        context['latest_posts'] = posts.exclude(pk=featured_post.pk) if featured_post else posts
        context['posts'] = posts
        return context


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'blogcms.BlogPostPage',
        related_name='tagged_items',
        on_delete=models.CASCADE,
    )


class BlogPostPage(Page):
    date = models.DateField(default=timezone.now)
    subtitle = models.CharField(max_length=255, blank=True)
    author_display_name = models.CharField(max_length=120, blank=True)
    featured = models.BooleanField(default=False)
    cover_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    excerpt = models.TextField(blank=True)
    body = RichTextField(
        blank=True,
        verbose_name='Legacy body',
        help_text='Legacy article body. Use the content blocks below for new posts.',
    )
    content = StreamField(
        [
            ('rich_text', blocks.RichTextBlock(features=BLOG_RICH_TEXT_FEATURES, label='Rich text')),
            ('code', BlogCodeBlock()),
            ('image', BlogImageBlock()),
            ('quote', blocks.BlockQuoteBlock(label='Quote')),
            ('callout', BlogCalloutBlock()),
        ],
        blank=True,
        use_json_field=True,
    )
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)

    parent_page_types = ['blogcms.BlogIndexPage']
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('subtitle'),
        FieldPanel('author_display_name'),
        FieldPanel('featured'),
        FieldPanel('cover_image'),
        FieldPanel('excerpt'),
        FieldPanel('tags'),
        FieldPanel('content'),
        FieldPanel('body'),
    ]

    search_fields = Page.search_fields + [
        index.SearchField('subtitle'),
        index.SearchField('excerpt'),
        index.SearchField('content'),
        index.SearchField('body'),
    ]

    @property
    def estimated_read_minutes(self):
        plain_text = ' '.join([self._stream_text(), re.sub(r'<[^>]+>', ' ', self.body or '')])
        words = re.findall(r'\w+', plain_text)
        return max(1, math.ceil(len(words) / 220))

    def _stream_text(self):
        parts = []
        for block in self.content:
            value = block.value
            if block.block_type in {'rich_text', 'quote'}:
                parts.append(re.sub(r'<[^>]+>', ' ', str(value)))
            elif block.block_type == 'code':
                parts.append(value.get('code', ''))
                parts.append(value.get('caption', ''))
            elif block.block_type == 'image':
                parts.append(value.get('caption', ''))
                parts.append(value.get('alt_text', ''))
            elif block.block_type == 'callout':
                parts.append(value.get('heading', ''))
                parts.append(re.sub(r'<[^>]+>', ' ', str(value.get('text', ''))))
        return ' '.join(parts)

    @property
    def display_author(self):
        if self.author_display_name:
            return self.author_display_name
        if self.owner:
            return self.owner.get_full_name() or self.owner.username
        return 'Caleb Mayaka'

    def related_posts(self, limit=3):
        base_posts = (
            BlogPostPage.objects.live()
            .public()
            .exclude(pk=self.pk)
            .select_related('cover_image', 'owner')
            .prefetch_related('tags')
        )
        tag_names = list(self.tags.names())
        related = []

        if tag_names:
            related = list(
                base_posts.filter(tags__name__in=tag_names)
                .annotate(match_count=Count('tags', filter=Q(tags__name__in=tag_names), distinct=True))
                .order_by('-match_count', '-date', '-first_published_at')
                .distinct()[:limit]
            )

        if len(related) < limit:
            related_ids = [post.pk for post in related]
            fallback = base_posts.exclude(pk__in=related_ids).order_by('-date', '-first_published_at')
            related.extend(list(fallback[: limit - len(related)]))

        return related

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['related_posts'] = self.related_posts()
        return context
