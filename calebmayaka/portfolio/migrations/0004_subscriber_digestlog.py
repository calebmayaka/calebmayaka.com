from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0003_siteprofile_whatsapp_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscriber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('is_confirmed', models.BooleanField(default=False)),
                ('confirm_token', models.CharField(editable=False, max_length=64, unique=True)),
                ('unsubscribe_token', models.CharField(editable=False, max_length=64, unique=True)),
                ('subscribed_at', models.DateTimeField(auto_now_add=True)),
                ('confirmed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Subscriber',
                'verbose_name_plural': 'Subscribers',
                'ordering': ['-subscribed_at'],
            },
        ),
        migrations.CreateModel(
            name='DigestLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=200)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('recipient_count', models.PositiveIntegerField(default=0)),
                ('post_count', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Digest log',
                'verbose_name_plural': 'Digest logs',
                'ordering': ['-sent_at'],
            },
        ),
    ]
