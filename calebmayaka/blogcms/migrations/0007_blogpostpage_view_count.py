from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blogcms', '0006_blogpostpage_noindex'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpostpage',
            name='view_count',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
    ]
