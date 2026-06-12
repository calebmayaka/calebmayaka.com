from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from blogcms.models import BlogVisit


class Command(BaseCommand):
    help = 'Delete blog visit analytics rows older than BLOG_VISIT_RETENTION_DAYS.'

    def handle(self, *args, **options):
        days = getattr(settings, 'BLOG_VISIT_RETENTION_DAYS', 90)
        cutoff = timezone.now() - timezone.timedelta(days=days)
        deleted, _ = BlogVisit.objects.filter(visited_at__lt=cutoff).delete()
        self.stdout.write(
            self.style.SUCCESS(
                f'Deleted {deleted} blog visit row(s) older than {days} days.'
            )
        )
