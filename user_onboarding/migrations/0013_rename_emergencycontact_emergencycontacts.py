# Generated by Django 5.1.6 on 2025-02-11 08:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_onboarding', '0012_alter_emergencycontact_patient'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='EmergencyContact',
            new_name='EmergencyContacts',
        ),
    ]
