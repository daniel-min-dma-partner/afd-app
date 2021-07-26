# Generated by Django 3.2.3 on 2021-07-08 21:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0003_remove_filemodel_user_specific_folder'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataflowCompareFilesModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file1', models.FileField(upload_to='documents/%Y/%m/%d')),
                ('file2', models.FileField(upload_to='documents/%Y/%m/%d')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
