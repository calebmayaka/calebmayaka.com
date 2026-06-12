from django.db import migrations


SOCIAL_LINKS = [
    {'label': 'GitHub', 'url': 'https://github.com/calebmayaka', 'order': 1},
    {'label': 'X / Twitter', 'url': 'https://x.com/ombogomayaka', 'order': 2},
]


def seed_social_links(apps, schema_editor):
    SocialLink = apps.get_model('portfolio', 'SocialLink')
    for data in SOCIAL_LINKS:
        SocialLink.objects.get_or_create(
            url=data['url'],
            defaults={'label': data['label'], 'order': data['order']},
        )


def remove_social_links(apps, schema_editor):
    SocialLink = apps.get_model('portfolio', 'SocialLink')
    SocialLink.objects.filter(url__in=[d['url'] for d in SOCIAL_LINKS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0004_subscriber_digestlog'),
    ]

    operations = [
        migrations.RunPython(seed_social_links, reverse_code=remove_social_links),
    ]
