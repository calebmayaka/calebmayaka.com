from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Inquiry, SiteProfile, SocialLink


SITE_CHROME_CACHE_KEY = 'portfolio:site_chrome:v1'


@receiver(post_save, sender=Inquiry)
def notify_owner_on_new_inquiry(sender, instance, created, **kwargs):
    if not created:
        return
    notify_email = getattr(settings, 'NOTIFY_EMAIL', None)
    if not notify_email:
        return
    subject = f'New inquiry: {instance.get_inquiry_type_display()} from {instance.email}'
    body = (
        f'New inquiry received.\n\n'
        f'Type: {instance.get_inquiry_type_display()}\n'
        f'From: {instance.email}\n'
        f'Date: {instance.created_at.strftime("%Y-%m-%d %H:%M UTC")}\n\n'
        f'Message:\n{instance.message}'
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[notify_email],
        fail_silently=True,
    )


@receiver([post_save, post_delete], sender=SiteProfile)
@receiver([post_save, post_delete], sender=SocialLink)
def clear_site_chrome_cache(sender, **kwargs):
    cache.delete(SITE_CHROME_CACHE_KEY)
