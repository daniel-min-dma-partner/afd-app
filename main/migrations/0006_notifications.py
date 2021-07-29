# Generated by Django 3.2.3 on 2021-07-22 15:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0005_filemodel_parent_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notifications',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=1024)),
                ('status',
                 models.IntegerField(choices=[(1, 'UNREAD_UNCLICKED'), (2, 'READ_UNCLIKED'), (3, 'READ_CLICKED')],
                                     default=1)),
                ('link', models.CharField(default='#', max_length=1024)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]