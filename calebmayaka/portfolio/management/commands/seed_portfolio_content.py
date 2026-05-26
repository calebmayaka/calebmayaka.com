from django.core.management.base import BaseCommand

from portfolio import data
from portfolio.models import (
    CaseStudy,
    Experience,
    NavItem,
    Project,
    Skill,
    SiteProfile,
    SocialLink,
    Stat,
    TechStack,
    Testimonial,
)


class Command(BaseCommand):
    help = 'Seed portfolio content from data.py into the database (idempotent).'

    def handle(self, *args, **options):
        self._seed_site_profile()
        self._seed_nav_items()
        self._seed_social_links()
        self._seed_stats()
        self._seed_skills()
        self._seed_tech_stack()
        self._seed_projects()
        self._seed_experience()
        self._seed_case_studies()
        self._seed_testimonials()
        self.stdout.write(self.style.SUCCESS('Portfolio content seeded successfully.'))

    def _seed_site_profile(self):
        d = data.profile
        _, created = SiteProfile.objects.update_or_create(
            pk=1,
            defaults={
                'name': d['name'],
                'initials': d['initials'],
                'role': d['role'],
                'headline': d['headline'],
                'summary': d['summary'],
                'location': d['location'],
                'email': d['email'],
                'whatsapp_url': d.get('whatsapp_url', ''),
                'availability': d['availability'],
                'meta_description': d['meta_description'],
            },
        )
        self._report('SiteProfile', created)

    def _seed_nav_items(self):
        for i, item in enumerate(data.nav_items):
            _, created = NavItem.objects.update_or_create(
                label=item['label'],
                defaults={
                    'url_name': item.get('url_name', ''),
                    'url': item.get('url', ''),
                    'order': i,
                },
            )
            self._report(f'NavItem:{item["label"]}', created)

    def _seed_social_links(self):
        for i, item in enumerate(data.social_links):
            _, created = SocialLink.objects.update_or_create(
                label=item['label'],
                defaults={'url': item['url'], 'order': i},
            )
            self._report(f'SocialLink:{item["label"]}', created)

    def _seed_stats(self):
        for i, item in enumerate(data.stats):
            _, created = Stat.objects.update_or_create(
                label=item['label'],
                defaults={'value': item['value'], 'order': i},
            )
            self._report(f'Stat:{item["label"]}', created)

    def _seed_skills(self):
        for i, item in enumerate(data.skills):
            _, created = Skill.objects.update_or_create(
                title=item['title'],
                defaults={
                    'description': item['description'],
                    'tags': item['tags'],
                    'order': i,
                },
            )
            self._report(f'Skill:{item["title"]}', created)

    def _seed_tech_stack(self):
        for i, name in enumerate(data.tech_stack):
            _, created = TechStack.objects.update_or_create(
                name=name,
                defaults={'order': i},
            )
            self._report(f'TechStack:{name}', created)

    def _seed_projects(self):
        for i, item in enumerate(data.projects):
            _, created = Project.objects.update_or_create(
                slug=item['id'],
                defaults={
                    'title': item['title'],
                    'category': item['category'],
                    'description': item['description'],
                    'tags': item['tags'],
                    'impact': item['impact'],
                    'status': item['status'],
                    'link': item['link'],
                    'repo': item['repo'],
                    'order': i,
                },
            )
            self._report(f'Project:{item["id"]}', created)

    def _seed_experience(self):
        for i, item in enumerate(data.experience):
            _, created = Experience.objects.update_or_create(
                role=item['role'],
                company=item['company'],
                defaults={
                    'period': item['period'],
                    'description': item['description'],
                    'achievements': item['achievements'],
                    'order': i,
                },
            )
            self._report(f'Experience:{item["role"]}', created)

    def _seed_case_studies(self):
        for i, item in enumerate(data.case_studies):
            _, created = CaseStudy.objects.update_or_create(
                slug=item['id'],
                defaults={
                    'title': item['title'],
                    'category': item['category'],
                    'duration': item['duration'],
                    'role': item['role'],
                    'description': item['description'],
                    'problem': item['problem'],
                    'solution': item['solution'],
                    'results': item['results'],
                    'tags': item['tags'],
                    'order': i,
                },
            )
            self._report(f'CaseStudy:{item["id"]}', created)

    def _seed_testimonials(self):
        for i, item in enumerate(data.testimonials):
            _, created = Testimonial.objects.update_or_create(
                name=item['name'],
                defaults={
                    'quote': item['quote'],
                    'title': item['title'],
                    'order': i,
                },
            )
            self._report(f'Testimonial:{item["name"]}', created)

    def _report(self, label, created):
        verb = 'Created' if created else 'Updated'
        self.stdout.write(f'  {verb}: {label}')
