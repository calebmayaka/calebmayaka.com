from datetime import date

from django.test import RequestFactory, TestCase, override_settings
from wagtail.models import Page

from .models import BlogIndexPage, BlogPostPage


@override_settings(ALLOWED_HOSTS=['127.0.0.1', 'testserver'])
class BlogPageContextTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/blog/')
        root = Page.objects.get(depth=1)
        self.index = BlogIndexPage(title='Articles', slug='articles')
        root.add_child(instance=self.index)

    def make_post(self, title, slug, post_date, featured=False, tags=None, content=None):
        post = BlogPostPage(
            title=title,
            slug=slug,
            date=post_date,
            featured=featured,
            excerpt=f'{title} excerpt',
            body='<p>Body copy for the test article.</p>',
            content=content or [],
        )
        self.index.add_child(instance=post)
        if tags:
            post.tags.add(*tags)
            post.save()
        return post

    def test_blog_index_context_uses_featured_post_when_available(self):
        self.make_post('Newest', 'newest', date(2026, 5, 3))
        featured = self.make_post('Featured', 'featured', date(2026, 5, 1), featured=True)

        context = self.index.get_context(self.request)

        self.assertEqual(context['featured_post'].pk, featured.pk)
        self.assertNotIn(featured, list(context['latest_posts']))

    def test_blog_index_context_falls_back_to_newest_post(self):
        older = self.make_post('Older', 'older', date(2026, 5, 1))
        newest = self.make_post('Newest', 'newest', date(2026, 5, 3))

        context = self.index.get_context(self.request)

        self.assertEqual(context['featured_post'].pk, newest.pk)
        self.assertIn(older, list(context['latest_posts']))

    def test_related_posts_exclude_current_article(self):
        current = self.make_post('Current', 'current', date(2026, 5, 4), tags=['django'])
        related = self.make_post('Related', 'related', date(2026, 5, 3), tags=['django'])

        related_posts = current.related_posts()

        self.assertIn(related, related_posts)
        self.assertNotIn(current, related_posts)

    def test_related_posts_prefer_shared_tags_then_fall_back_to_latest(self):
        current = self.make_post('Current', 'current', date(2026, 5, 4), tags=['django'])
        fallback = self.make_post('Fallback', 'fallback', date(2026, 5, 3), tags=['design'])
        tagged = self.make_post('Tagged', 'tagged', date(2026, 5, 2), tags=['django'])

        related_posts = current.related_posts(limit=2)

        self.assertEqual([post.pk for post in related_posts], [tagged.pk, fallback.pk])

    def test_article_page_renders_streamfield_code_blocks(self):
        post = self.make_post(
            'Code Post',
            'code-post',
            date(2026, 5, 5),
            content=[
                ('rich_text', '<p>Intro copy.</p>'),
                ('code', {
                    'filename': 'example.py',
                    'language': 'python',
                    'code': 'print("hello")',
                    'caption': 'A short Python example.',
                }),
            ],
        )

        request = RequestFactory().get('/articles/code-post/')
        response = post.serve(request)
        response.render()

        html = response.content.decode()
        self.assertIn('example.py', html)
        self.assertIn('print(&quot;hello&quot;)', html)
        self.assertIn('data-copy-code', html)
