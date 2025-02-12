# Generated by Django 4.2.3 on 2025-02-08 06:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_onboarding', '0002_alter_customuser_phone'),
    ]

    operations = [
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dob', models.DateField(verbose_name='Date of Birth')),
                ('full_name', models.CharField(blank=True, max_length=100, null=True)),
                ('gender', models.CharField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], max_length=10)),
                ('address', models.TextField(verbose_name='Address')),
                ('blood_group', models.CharField(choices=[('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')], max_length=3)),
                ('height', models.PositiveIntegerField(help_text='Height in cm')),
                ('weight', models.PositiveIntegerField(help_text='Weight in kg')),
                ('id_proof', models.FileField(upload_to='id_proofs/')),
                ('usual_wake_up_time', models.TimeField()),
                ('current_location_status', models.CharField(choices=[('AtHome', 'At Home'), ('Travelling', 'Travelling')], max_length=50)),
                ('expected_return_date', models.DateField(blank=True, null=True)),
                ('phone', models.CharField(blank=True, max_length=15)),
                ('alternate_phone', models.CharField(blank=True, max_length=15)),
                ('pin_code', models.CharField(blank=True, max_length=15)),
            ],
        ),
        migrations.AlterField(
            model_name='customuser',
            name='phone',
            field=models.CharField(max_length=15, unique=True),
        ),
        migrations.CreateModel(
            name='PreferredMedicalServices',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preferred_doctor_name', models.CharField(blank=True, max_length=100, null=True)),
                ('doctor_contact_number', models.CharField(blank=True, max_length=15, null=True)),
                ('preferred_hospital_or_clinic', models.CharField(blank=True, max_length=100, null=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preferred_medical_services', to='user_onboarding.patient')),
            ],
        ),
        migrations.AddField(
            model_name='patient',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='patient_profile', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='MedicalHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('existing_health_conditions', models.TextField(blank=True, help_text='List any chronic illnesses', null=True)),
                ('known_allergies', models.TextField(blank=True, help_text='Food, medication, environmental allergies', null=True)),
                ('current_prescriptions', models.FileField(blank=True, null=True, upload_to='prescriptions/')),
                ('past_surgeries', models.TextField(blank=True, help_text='Include dates if available', null=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='medical_histories', to='user_onboarding.patient')),
            ],
        ),
        migrations.CreateModel(
            name='LifestyleDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_level', models.CharField(blank=True, choices=[('Low', 'Low'), ('Moderate', 'Moderate'), ('High', 'High')], max_length=10, null=True)),
                ('diet_preferences', models.CharField(blank=True, choices=[('Vegetarian', 'Vegetarian'), ('Non-Vegetarian', 'Non-Vegetarian'), ('Vegan', 'Vegan')], max_length=15, null=True)),
                ('requires_mobility_assistance', models.BooleanField(default=False)),
                ('has_vision_impairment', models.BooleanField(default=False)),
                ('has_hearing_impairment', models.BooleanField(default=False)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lifestyle_details', to='user_onboarding.patient')),
            ],
        ),
        migrations.CreateModel(
            name='EmergencyContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('next_of_kin_name', models.CharField(max_length=100)),
                ('next_of_kin_contact_number', models.CharField(max_length=15)),
                ('relationship_with_senior', models.CharField(max_length=50)),
                ('neighbor_name', models.CharField(blank=True, max_length=100, null=True)),
                ('neighbor_contact_number', models.CharField(blank=True, max_length=15, null=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emergency_contacts', to='user_onboarding.patient')),
            ],
        ),
    ]
