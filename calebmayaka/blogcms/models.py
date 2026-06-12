import ipaddress
import logging
import math
import re
from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.db.models import Count, F, Q
from django.utils import timezone
from django.utils.functional import cached_property
from portfolio.models import SiteProfile, SocialLink
from modelcluster.fields import ParentalKey
from modelcluster.tags import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail import blocks
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.contrib.table_block.blocks import TableBlock as WagtailTableBlock
from wagtail.images import get_image_model_string
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Page
from wagtail.search import index

from .utils import is_supported_video_url


logger = logging.getLogger(__name__)

BOT_USER_AGENT_TOKENS = (
    'bot',
    'crawl',
    'spider',
    'slurp',
    'bingpreview',
    'facebookexternalhit',
    'whatsapp',
    'telegrambot',
    'linkedinbot',
    'preview',
)


def get_client_ip(request):
    ip_sources = (
        ('HTTP_CF_CONNECTING_IP', 'cf-connecting-ip'),
        ('HTTP_X_FORWARDED_FOR', 'x-forwarded-for'),
        ('REMOTE_ADDR', 'remote-addr'),
    )
    for header, source in ip_sources:
        value = request.META.get(header, '').strip()
        if not value:
            continue
        candidate = value.split(',', 1)[0].strip()
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            continue
        return candidate, source
    return '', ''


def is_likely_bot_user_agent(user_agent):
    normalized = (user_agent or '').lower()
    return any(token in normalized for token in BOT_USER_AGENT_TOKENS)


@lru_cache(maxsize=2)
def geoip_reader(geoip_path):
    from django.contrib.gis.geoip2 import GeoIP2

    return GeoIP2(path=geoip_path)


def lookup_geoip_location(ip_address):
    geoip_path = getattr(settings, 'GEOIP_PATH', '')
    if not geoip_path or not ip_address:
        return {}

    try:
        result = geoip_reader(geoip_path).city(ip_address)
    except Exception as exc:
        logger.debug('Blog visit GeoIP lookup skipped: %s', exc)
        return {}

    return {
        'country_code': result.get('country_code') or '',
        'country_name': result.get('country_name') or '',
        'region': result.get('region') or result.get('region_name') or '',
        'city': result.get('city') or '',
        'latitude': result.get('latitude'),
        'longitude': result.get('longitude'),
    }


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


class BlogVideoBlock(blocks.StructBlock):
    """YouTube or Vimeo embed with optional caption and native lazy-loading."""
    url = blocks.URLBlock(
        label='Video URL',
        help_text='YouTube or Vimeo URL — e.g. https://www.youtube.com/watch?v=…',
    )
    caption = blocks.CharBlock(required=False, max_length=220)

    def clean(self, value):
        result = super().clean(value)
        if not is_supported_video_url(result.get('url')):
            raise StructBlockValidationError({
                'url': ValidationError('Enter a supported YouTube or Vimeo URL.'),
            })
        return result

    class Meta:
        icon = 'media'
        label = 'Video embed'


class BlogTweetBlock(blocks.StructBlock):
    """Embed a tweet / X post by its full URL."""
    tweet_url = blocks.URLBlock(
        label='Tweet / X post URL',
        help_text='Full URL, e.g. https://twitter.com/user/status/123456789',
    )

    class Meta:
        icon = 'link'
        label = 'Tweet / X post'


class BlogMathBlock(blocks.StructBlock):
    """Render a LaTeX expression via KaTeX in the browser."""
    latex = blocks.TextBlock(
        label='LaTeX expression',
        help_text='Standard LaTeX math — e.g. \\frac{1}{2} or E = mc^2',
    )
    display = blocks.ChoiceBlock(
        choices=[
            ('block', 'Block (display mode, centred)'),
            ('inline', 'Inline'),
        ],
        default='block',
        label='Display mode',
    )

    class Meta:
        icon = 'snippet'
        label = 'Math / LaTeX'


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)
    POSTS_PER_PAGE = 6

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
        remaining = posts.exclude(pk=featured_post.pk) if featured_post else posts

        paginator = Paginator(remaining, self.POSTS_PER_PAGE)
        page_num = request.GET.get('page', 1)
        try:
            page_obj = paginator.page(page_num)
        except (EmptyPage, PageNotAnInteger):
            page_obj = paginator.page(max(1, paginator.num_pages))

        context['featured_post'] = featured_post if page_obj.number == 1 else None
        context['latest_posts'] = page_obj
        context['page_obj'] = page_obj
        context['paginator'] = paginator
        context['posts'] = posts
        return context


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'blogcms.BlogPostPage',
        related_name='tagged_items',
        on_delete=models.CASCADE,
    )


class BlogVisit(models.Model):
    post = models.ForeignKey(
        'blogcms.BlogPostPage',
        related_name='visits',
        on_delete=models.CASCADE,
    )
    visited_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField()
    ip_source = models.CharField(max_length=40, blank=True)
    user_agent = models.TextField(blank=True)
    referer = models.URLField(max_length=1000, blank=True)
    path = models.CharField(max_length=1000, blank=True)
    country_code = models.CharField(max_length=8, blank=True)
    country_name = models.CharField(max_length=120, blank=True)
    region = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=120, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_unique_cookie = models.BooleanField(default=False)
    is_likely_bot = models.BooleanField(default=False)

    class Meta:
        ordering = ['-visited_at']
        indexes = [
            models.Index(fields=['visited_at'], name='blogvisit_visited_at_idx'),
            models.Index(fields=['post', 'visited_at'], name='blogvisit_post_time_idx'),
            models.Index(fields=['ip_address'], name='blogvisit_ip_idx'),
            models.Index(fields=['country_code'], name='blogvisit_country_idx'),
        ]

    def __str__(self):
        return f'{self.post.title} visit from {self.ip_address}'

    @property
    def location_label(self):
        return ', '.join(
            part for part in (self.city, self.region, self.country_name) if part
        ) or 'Unknown'


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
            ('video', BlogVideoBlock()),
            ('tweet', BlogTweetBlock()),
            ('table', WagtailTableBlock(label='Table')),
            ('math', BlogMathBlock()),
        ],
        blank=True,
        use_json_field=True,
    )
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    view_count = models.PositiveIntegerField(default=0, editable=False)
    noindex = models.BooleanField(
        default=False,
        help_text='Exclude this page from search engine indexes.',
    )

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

    promote_panels = Page.promote_panels + [
        FieldPanel('noindex'),
        MultiFieldPanel(
            [
                FieldPanel('go_live_at'),
                FieldPanel('expire_at'),
            ],
            heading='Scheduled publishing',
            help_text=(
                'Set a future date to auto-publish, or an expiry date to unpublish. '
                'Run "python manage.py publish_scheduled_pages" on a cron to activate.'
            ),
        ),
    ]

    search_fields = Page.search_fields + [
        index.SearchField('title', boost=10),
        index.AutocompleteField('title'),
        index.SearchField('subtitle', boost=5),
        index.AutocompleteField('subtitle'),
        index.SearchField('excerpt', boost=3),
        index.SearchField('content'),
        index.SearchField('body'),
        index.FilterField('date'),
        index.FilterField('first_published_at'),
    ]

    @cached_property
    def estimated_read_minutes(self):
        plain_text = ' '.join([self._stream_text(), re.sub(r'<[^>]+>', ' ', self.body or '')])
        words = re.findall(r'\w+', plain_text)
        return max(1, math.ceil(len(words) / 220))

    @cached_property
    def _content_block_types(self):
        return {block.block_type for block in self.content}

    @cached_property
    def has_code_blocks(self):
        return 'code' in self._content_block_types or '<pre' in (self.body or '')

    @cached_property
    def has_math_blocks(self):
        return 'math' in self._content_block_types

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
            elif block.block_type == 'video':
                parts.append(value.get('caption', ''))
            elif block.block_type == 'math':
                parts.append(value.get('latex', ''))
            elif block.block_type == 'table':
                # Extract cell text from the table data rows
                try:
                    for row in (value.get('data') or []):
                        for cell in (row or []):
                            if cell:
                                parts.append(str(cell))
                except Exception:
                    pass
        return ' '.join(parts)

    @property
    def display_author(self):
        if self.author_display_name:
            return self.author_display_name
        if self.owner:
            return self.owner.get_full_name() or self.owner.username
        return 'Caleb Mayaka'

    def related_posts(self, limit=3):
        parent = self.get_parent()
        base_posts = (
            BlogPostPage.objects.live()
            .public()
            .descendant_of(parent)
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

    def get_sitemap_urls(self, request=None):
        if self.noindex:
            return []
        return super().get_sitemap_urls(request)

    def _record_visit(self, request, is_unique_cookie):
        ip_address, ip_source = get_client_ip(request)
        if not ip_address:
            return

        user_agent = request.META.get('HTTP_USER_AGENT', '')
        geo_fields = lookup_geoip_location(ip_address)
        BlogVisit.objects.create(
            post=self,
            ip_address=ip_address,
            ip_source=ip_source,
            user_agent=user_agent[:2000],
            referer=request.META.get('HTTP_REFERER', '')[:1000],
            path=request.get_full_path()[:1000],
            is_unique_cookie=is_unique_cookie,
            is_likely_bot=is_likely_bot_user_agent(user_agent),
            **geo_fields,
        )

    def serve(self, request, *args, **kwargs):
        # Count every unique visit (deduplicated by cookie so refreshes do not inflate).
        # Skip Wagtail preview requests.
        cookie_name = 'blog_viewed_posts'
        viewed = {
            int(value)
            for value in request.COOKIES.get(cookie_name, '').split(',')
            if value.isdigit()
        }
        should_set_view_cookie = False

        if not getattr(request, 'is_preview', False):
            is_unique_cookie = self.pk not in viewed
            if is_unique_cookie:
                BlogPostPage.objects.filter(pk=self.pk).update(
                    view_count=F('view_count') + 1
                )
                # Reflect the increment on the in-memory instance so the
                # template shows the updated count immediately.
                self.view_count += 1
                viewed.add(self.pk)
                should_set_view_cookie = True
            try:
                self._record_visit(request, is_unique_cookie=is_unique_cookie)
            except Exception:
                logger.exception('Failed to record blog visit for post %s.', self.pk)

        response = super().serve(request, *args, **kwargs)
        if should_set_view_cookie:
            response.set_cookie(
                cookie_name,
                ','.join(str(pk) for pk in sorted(viewed)),
                max_age=60 * 60 * 24 * 365,
                secure=request.is_secure(),
                samesite='Lax',
            )
        return response

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        parent = self.get_parent()
        context['related_posts'] = self.related_posts()
        context['prev_post'] = (
            BlogPostPage.objects.live().public()
            .descendant_of(parent)
            .filter(date__lt=self.date)
            .order_by('-date').first()
        )
        context['next_post'] = (
            BlogPostPage.objects.live().public()
            .descendant_of(parent)
            .filter(date__gt=self.date)
            .order_by('date').first()
        )
        context['site_profile'] = SiteProfile.objects.first()
        context['social_links'] = SocialLink.objects.order_by('order')
        return context
