# Generated by Django 5.1.6 on 2025-02-23 11:20

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_onboarding', '0017_alter_communityevent_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='LabReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test_name', models.CharField(max_length=255)),
                ('test_date', models.DateField()),
                ('LR_file_url', models.URLField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lab_reports', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Prescription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Presc_file_url', models.URLField()),
                ('doctor_name', models.CharField(max_length=255)),
                ('prescribed_date', models.DateField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prescriptions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
