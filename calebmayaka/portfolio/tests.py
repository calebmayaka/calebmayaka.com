from datetime import date
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from wagtail.models import Site

from blogcms.models import BlogIndexPage, BlogPostPage
from portfolio.models import Inquiry, Project, SiteProfile, Skill


@override_settings(
    ALLOWED_HOSTS=['testserver'],
    SECURE_SSL_REDIRECT=False,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    NOTIFY_EMAIL='owner@example.com',
    RATELIMIT_ENABLE=False,
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    },
)
class HomepageTests(TestCase):
    def setUp(self):
        Project.objects.all().delete()
        SiteProfile.objects.create(
            name='Caleb Mayaka',
            initials='CM',
            role='Software engineer',
            headline='Software that ships.',
            summary='A software engineer who builds practical systems. Based in Nairobi.',
            location='Nairobi',
            email='hello@example.com',
            availability='Available',
            meta_description='Projects and writing by Caleb Mayaka.',
        )
        self.inquiry = {
            'email': 'visitor@example.com',
            'inquiry_type': Inquiry.WEBSITE,
            'message': 'I would like to discuss a new website.',
        }

    def test_homepage_renders_without_projects_or_articles(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Building.')
        self.assertContains(response, 'Articles will appear here as they are published.')
        self.assertEqual(response.context['home_active_tab'], 'writing')

    def test_homepage_hides_projects_and_limits_published_articles(self):
        Project.objects.bulk_create([
            Project(
                slug=f'project-{number}',
                title=f'Project {number}',
                category='Software',
                link=f'https://private-project.example/{number}',
                order=number,
            )
            for number in range(10)
        ])
        index = BlogIndexPage(title='Writing', slug='writing')
        Site.objects.get(is_default_site=True).root_page.add_child(instance=index)
        for number in range(6):
            index.add_child(instance=BlogPostPage(
                title=f'Article {number}',
                slug=f'article-{number}',
                date=date(2026, 7, number + 1),
            ))
        index.add_child(instance=BlogPostPage(title='Unpublished article', slug='unpublished', live=False))

        response = self.client.get(reverse('home'))

        self.assertNotIn('projects', response.context)
        self.assertEqual(len(response.context['blog_posts']), 5)
        self.assertNotContains(response, 'Project 0')
        self.assertNotContains(response, 'private-project.example')
        self.assertNotContains(response, 'data-home-tab="work"')
        self.assertNotContains(response, 'id="work"')
        self.assertNotContains(response, 'Software I build and run.')
        self.assertEqual(Project.objects.count(), 10)
        self.assertNotContains(response, 'Unpublished article')
        self.assertNotContains(response, 'Article 0')

    def test_project_editor_requires_login(self):
        response = self.client.get(reverse('dev_content_list', kwargs={'content_type': 'projects'}))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('dashboard_login')))

    def test_about_combines_expertise_and_remaining_tools(self):
        Skill.objects.all().delete()
        Skill.objects.create(title='Microsoft Dynamics NAV', description='ERP customization.', order=0)
        Skill.objects.create(title='Django REST Framework', description='REST APIs.', order=1)
        Skill.objects.create(title='Python & Django', description='APIs with Django REST Framework and PostgreSQL.')
        response = self.client.get(reverse('home'))

        self.assertNotContains(response, 'data-home-tab="stack"')
        self.assertNotContains(response, 'data-home-panel="stack"')
        self.assertContains(response, 'Also in my toolkit')
        self.assertEqual([skill.title for skill in response.context['skills']][:2], ['Python & Django', 'Django REST Framework'])
        categories = {category['name']: category['items'] for category in response.context['stack_categories']}
        self.assertEqual(categories['Languages'], 'Rust, SQL, JavaScript')
        self.assertNotIn('Backend', categories)
        self.assertContains(response, 'Photoshop, Premiere Pro, After Effects')
        self.assertContains(response, 'A software engineer who builds practical systems.')
        self.assertContains(response, 'Based in Nairobi.')

    def test_inquiry_confirmation_returns_to_contact(self):
        response = self.client.post(reverse('home'), self.inquiry, follow=True)

        self.assertEqual(response.redirect_chain, [('/#contact', 302)])
        self.assertEqual(Inquiry.objects.get().email, self.inquiry['email'])
        self.assertEqual(response.context['home_active_tab'], 'contact')
        self.assertContains(response, 'Your inquiry has been sent successfully.')
        self.assertEqual(len(mail.outbox), 1)

    def test_invalid_inquiry_keeps_values_and_opens_contact(self):
        response = self.client.post(reverse('home'), {**self.inquiry, 'email': 'invalid'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['home_active_tab'], 'contact')
        self.assertTrue(response.context['inquiry_form'].is_bound)
        self.assertIn('email', response.context['inquiry_form'].errors)
        self.assertContains(response, self.inquiry['message'])
        self.assertFalse(Inquiry.objects.exists())

    def test_empty_post_is_validated_in_contact(self):
        response = self.client.post(reverse('home'), {})

        self.assertEqual(response.context['home_active_tab'], 'contact')
        self.assertEqual(set(response.context['inquiry_form'].errors), {'email', 'inquiry_type', 'message'})

    def test_honeypot_does_not_save_or_send_email(self):
        response = self.client.post(reverse('home'), {**self.inquiry, 'website': 'spam.example'})

        self.assertRedirects(response, '/#contact', fetch_redirect_response=False)
        self.assertFalse(Inquiry.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_limited_inquiry_returns_to_contact_without_saving(self):
        with patch('django_ratelimit.decorators.is_ratelimited', return_value=True):
            response = self.client.post(reverse('home'), self.inquiry, follow=True)

        self.assertEqual(response.redirect_chain, [('/#contact', 302)])
        self.assertContains(response, 'Too many submissions.')
        self.assertEqual(response.context['home_active_tab'], 'contact')
        self.assertFalse(Inquiry.objects.exists())

    def test_about_keeps_its_existing_navigation_and_footer(self):
        response = self.client.get(reverse('about'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="site-nav"')
        self.assertContains(response, 'class="site-footer"')
        self.assertNotContains(response, 'portfolio/css/home.css')
