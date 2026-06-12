import logging
from datetime import datetime, timezone

from django.contrib.syndication.views import Feed

from .models import BlogIndexPage, BlogPostPage

logger = logging.getLogger(__name__)


class LatestBlogPostsFeed(Feed):
    title = 'calebmayaka.com — Blog'
    description = 'Essays, notes, and technical writing from calebmayaka.com.'

    def link(self):
        index = BlogIndexPage.objects.live().public().first()
        return index.url if index else '/blog/'

    def items(self):
        return (
            BlogPostPage.objects.live()
            .public()
            .select_related('owner')
            .order_by('-date', '-first_published_at')[:20]
        )

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        import html as _html
        parts = []
        try:
            for block in item.content:
                if block.block_type == 'rich_text':
                    parts.append(str(block.value))
                elif block.block_type == 'quote':
                    parts.append('<blockquote><p>{}</p></blockquote>'.format(
                        _html.escape(str(block.value))
                    ))
                elif block.block_type == 'code':
                    lang = block.value.get('language', 'text')
                    code = _html.escape(block.value.get('code', ''))
                    filename = block.value.get('filename', '')
                    caption = block.value.get('caption', '')
                    header = '<p><small>{}</small></p>'.format(_html.escape(filename)) if filename else ''
                    footer = '<p><small>{}</small></p>'.format(_html.escape(caption)) if caption else ''
                    parts.append('{}<pre><code class="language-{}">{}</code></pre>{}'.format(
                        header, lang, code, footer
                    ))
                elif block.block_type == 'callout':
                    heading = _html.escape(block.value.get('heading', ''))
                    text = str(block.value.get('text', ''))
                    h = '<strong>{}</strong>'.format(heading) if heading else ''
                    parts.append('<blockquote>{}{}</blockquote>'.format(h, text))
            if item.body:
                from wagtail.rich_text import expand_db_html
                parts.append(expand_db_html(item.body))
        except Exception:
            # A corrupted block or deleted image reference must not 500 the
            # entire feed for every subscriber.  Fall back gracefully.
            logger.exception('Feed description render failed for post pk=%s', item.pk)
            parts = []
        return '\n'.join(parts) if parts else (item.excerpt or item.subtitle or '')

    def item_link(self, item):
        return item.full_url

    def item_pubdate(self, item):
        return datetime(item.date.year, item.date.month, item.date.day, tzinfo=timezone.utc)

    def item_author_name(self, item):
        return item.display_author
