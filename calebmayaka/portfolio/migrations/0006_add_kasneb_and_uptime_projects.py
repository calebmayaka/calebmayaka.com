from django.db import migrations


PROJECTS = [
    {
        'slug': 'kasneb-revision-guides',
        'title': 'KASNEB Revision Guides',
        'category': 'Education platform',
        'description': 'A digital reading platform for official KASNEB revision guides, with student sign-in and access to guides purchased through the student portal.',
        'tags': ['React', 'Revision guides', 'Digital reading'],
        'impact': 'Gives KASNEB students a dedicated place to access and read their official revision guides.',
        'status': 'Live',
        'link': 'https://revision.kasneb.or.ke',
        'repo': '#',
    },
    {
        'slug': 'kasneb-student-portal',
        'title': 'KASNEB Student Portal',
        'category': 'Student services',
        'description': 'An online self-service portal for KASNEB students, bringing account access, exam bookings, and revision-guide purchases into one place.',
        'tags': ['Student services', 'Exam bookings', 'Self-service'],
        'impact': 'Centralizes student services and access to KASNEB learning resources.',
        'status': 'Live',
        'link': 'https://online.kasneb.or.ke',
        'repo': '#',
    },
    {
        'slug': 'pulse-uptime',
        'title': 'Pulse Uptime',
        'category': 'Uptime monitoring',
        'description': 'A self-hosted dashboard for monitoring website availability, with background health checks, incident history, and email alerts for outages and recovery.',
        'tags': ['Node.js', 'SQLite', 'Email alerts'],
        'impact': 'Keeps service health and outage notifications in one dashboard, hosted on my own server.',
        'status': 'Live',
        'link': 'https://uptime.calebmayaka.com',
        'repo': '#',
    },
]


def add_projects(apps, schema_editor):
    Project = apps.get_model('portfolio', 'Project')
    projects = Project.objects.using(schema_editor.connection.alias)
    last_order = projects.order_by('-order').values_list('order', flat=True).first()
    next_order = last_order + 1 if last_order is not None else 0

    for project in PROJECTS:
        _, created = projects.get_or_create(
            slug=project['slug'],
            defaults={
                **{key: value for key, value in project.items() if key != 'slug'},
                'order': next_order,
            },
        )
        if created:
            next_order += 1


class Migration(migrations.Migration):
    dependencies = [
        ('portfolio', '0005_seed_social_links'),
    ]

    operations = [
        migrations.RunPython(add_projects, reverse_code=migrations.RunPython.noop),
    ]
