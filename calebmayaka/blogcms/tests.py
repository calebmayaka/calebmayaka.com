from datetime import date
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from portfolio.models import DashboardUserProfile, SiteProfile
from wagtail.models import Page

from .utils import embed_url
from .models import BlogIndexPage, BlogPostPage, BlogVisit


@override_settings(
    ALLOWED_HOSTS=['127.0.0.1', 'testserver'],
    SECURE_SSL_REDIRECT=False,
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)
class BlogPageContextTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/blog/')
        SiteProfile.objects.create(
            name='Caleb Mayaka',
            initials='CM',
            role='Developer',
            headline='Test headline',
            summary='Test summary',
            location='Nairobi',
            email='caleb@example.com',
            availability='Available',
            meta_description='Test portfolio',
        )
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

    def test_blog_index_renders_single_featured_post(self):
        self.make_post('Only Post', 'only-post', date(2026, 5, 3), featured=True)

        response = self.index.serve(RequestFactory().get('/articles/'))
        response.render()

        html = response.content.decode()
        self.assertIn('Only Post', html)
        self.assertNotIn('Articles are being prepared', html)

    def test_noindex_post_is_excluded_from_sitemap(self):
        post = self.make_post('Private Draft', 'private-draft', date(2026, 5, 3))
        post.noindex = True

        self.assertEqual(post.get_sitemap_urls(), [])

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

    def test_related_posts_stay_within_current_blog_index(self):
        current = self.make_post('Current', 'current', date(2026, 5, 4), tags=['django'])

        root = Page.objects.get(depth=1)
        other_index = BlogIndexPage(title='Other Articles', slug='other-articles')
        root.add_child(instance=other_index)
        other_post = BlogPostPage(
            title='Other Post',
            slug='other-post',
            date=date(2026, 5, 3),
        )
        other_index.add_child(instance=other_post)
        other_post.tags.add('django')
        other_post.save()

        self.assertNotIn(other_post, current.related_posts())

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

    def test_youtube_embed_url_includes_origin(self):
        url = embed_url(
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://www.calebmayaka.com',
        )

        self.assertEqual(
            url,
            'https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0&origin=https%3A%2F%2Fwww.calebmayaka.com',
        )

    def test_article_page_logs_blog_visit(self):
        post = self.make_post('Tracked Post', 'tracked-post', date(2026, 5, 6))
        request = RequestFactory().get(
            '/articles/tracked-post/',
            REMOTE_ADDR='203.0.113.10',
            HTTP_USER_AGENT='Mozilla/5.0',
            HTTP_REFERER='https://example.com/source',
        )

        response = post.serve(request)
        response.render()

        visit = BlogVisit.objects.get()
        self.assertEqual(visit.post, post)
        self.assertEqual(visit.ip_address, '203.0.113.10')
        self.assertEqual(visit.ip_source, 'remote-addr')
        self.assertEqual(visit.referer, 'https://example.com/source')
        self.assertTrue(visit.is_unique_cookie)

    def test_wagtail_preview_does_not_log_blog_visit(self):
        post = self.make_post('Preview Post', 'preview-post', date(2026, 5, 6))
        request = RequestFactory().get('/articles/preview-post/', REMOTE_ADDR='203.0.113.11')
        request.is_preview = True

        response = post.serve(request)
        response.render()

        self.assertFalse(BlogVisit.objects.exists())

    @override_settings(GEOIP_PATH='C:/missing-geoip-db')
    def test_missing_geoip_database_does_not_500(self):
        post = self.make_post('GeoIP Post', 'geoip-post', date(2026, 5, 6))
        request = RequestFactory().get('/articles/geoip-post/', REMOTE_ADDR='203.0.113.12')

        response = post.serve(request)
        response.render()

        visit = BlogVisit.objects.get()
        self.assertEqual(visit.country_code, '')
        self.assertEqual(visit.city, '')

    def test_cf_connecting_ip_wins_over_forwarded_and_remote_addr(self):
        post = self.make_post('IP Post', 'ip-post', date(2026, 5, 6))
        request = RequestFactory().get(
            '/articles/ip-post/',
            HTTP_CF_CONNECTING_IP='198.51.100.20',
            HTTP_X_FORWARDED_FOR='198.51.100.21, 198.51.100.22',
            REMOTE_ADDR='198.51.100.23',
        )

        response = post.serve(request)
        response.render()

        visit = BlogVisit.objects.get()
        self.assertEqual(visit.ip_address, '198.51.100.20')
        self.assertEqual(visit.ip_source, 'cf-connecting-ip')

    def test_repeated_browser_cookie_marks_not_unique_but_still_logs(self):
        post = self.make_post('Repeat Post', 'repeat-post', date(2026, 5, 6))
        first_request = RequestFactory().get('/articles/repeat-post/', REMOTE_ADDR='198.51.100.30')
        second_request = RequestFactory().get('/articles/repeat-post/', REMOTE_ADDR='198.51.100.30')
        second_request.COOKIES['blog_viewed_posts'] = str(post.pk)

        first_response = post.serve(first_request)
        first_response.render()
        second_response = post.serve(second_request)
        second_response.render()

        visits = list(BlogVisit.objects.order_by('visited_at'))
        self.assertEqual(len(visits), 2)
        self.assertTrue(visits[0].is_unique_cookie)
        self.assertFalse(visits[1].is_unique_cookie)

    def test_purge_blog_visits_command_deletes_only_expired_rows(self):
        post = self.make_post('Purge Post', 'purge-post', date(2026, 5, 6))
        old_visit = BlogVisit.objects.create(post=post, ip_address='198.51.100.40')
        new_visit = BlogVisit.objects.create(post=post, ip_address='198.51.100.41')
        BlogVisit.objects.filter(pk=old_visit.pk).update(
            visited_at=timezone.now() - timezone.timedelta(days=91)
        )
        out = StringIO()

        call_command('purge_blog_visits', stdout=out)

        self.assertIn('Deleted 1 blog visit row', out.getvalue())
        self.assertFalse(BlogVisit.objects.filter(pk=old_visit.pk).exists())
        self.assertTrue(BlogVisit.objects.filter(pk=new_visit.pk).exists())

    def test_blog_analytics_requires_authentication(self):
        response = self.client.get(reverse('dev_blog_analytics'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('dashboard_login'), response['Location'])

    def test_authenticated_user_without_dashboard_profile_is_not_auto_authorized(self):
        user = User.objects.create_user(
            username='plain@example.com',
            email='plain@example.com',
            password='test-password',
        )
        self.client.login(username='plain@example.com', password='test-password')

        response = self.client.get(reverse('dev'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('dashboard_login'))
        self.assertFalse(DashboardUserProfile.objects.filter(user=user).exists())

    def test_dashboard_user_can_view_blog_analytics(self):
        self.login_dashboard_user(role=DashboardUserProfile.ADMIN)

        response = self.client.get(reverse('dev_blog_analytics'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Article Visits')

    def test_manager_cannot_view_blog_analytics(self):
        self.login_dashboard_user()

        response = self.client.get(reverse('dev_blog_analytics'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('dev'))

    def test_blog_analytics_filters_by_post_country_search_and_range(self):
        user = self.login_dashboard_user(role=DashboardUserProfile.ADMIN)
        matching_post = self.make_post('Kenya Post', 'kenya-post', date(2026, 5, 6))
        other_post = self.make_post('Other Post', 'other-post', date(2026, 5, 6))
        BlogVisit.objects.create(
            post=matching_post,
            ip_address='198.51.100.50',
            country_code='KE',
            country_name='Kenya',
            city='Nairobi',
            user_agent='Mozilla/5.0',
        )
        BlogVisit.objects.create(
            post=other_post,
            ip_address='198.51.100.51',
            country_code='US',
            country_name='United States',
            city='Boston',
            user_agent='Mozilla/5.0',
        )

        response = self.client.get(
            reverse('dev_blog_analytics'),
            {
                'range': '90d',
                'post': str(matching_post.pk),
                'country': 'KE',
                'q': 'Nairobi',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kenya Post')
        self.assertContains(response, 'Nairobi')
        self.assertNotContains(response, 'Boston')
        self.assertEqual(user.dashboard_profile.role, DashboardUserProfile.ADMIN)

    def test_blog_analytics_paginates_recent_visits(self):
        self.login_dashboard_user(role=DashboardUserProfile.ADMIN)
        post = self.make_post('Paged Post', 'paged-post', date(2026, 5, 6))
        for index in range(55):
            BlogVisit.objects.create(
                post=post,
                ip_address=f'198.51.100.{index + 1}',
                user_agent='Mozilla/5.0',
            )

        response = self.client.get(reverse('dev_blog_analytics'))
        second_page = self.client.get(reverse('dev_blog_analytics'), {'page': '2'})

        self.assertContains(response, 'Page 1 of 2')
        self.assertContains(response, 'Next')
        self.assertContains(second_page, 'Page 2 of 2')
        self.assertContains(second_page, 'Previous')

    def login_dashboard_user(self, role=DashboardUserProfile.MANAGER):
        user = User.objects.create_user(
            username='manager@example.com',
            email='manager@example.com',
            password='test-password',
        )
        DashboardUserProfile.objects.create(
            user=user,
            role=role,
        )
        self.client.login(username='manager@example.com', password='test-password')
        return user
