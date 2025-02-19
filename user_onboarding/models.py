from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group
from django.db import models
import uuid
class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, email=None, password=None, role="USERS"):
        if not phone_number:
            raise ValueError("Phone number is required")
        username = email.split("@")[0] if email else f"user_{uuid.uuid4().hex[:8]}"
        user = self.model(phone_number=phone_number, email=self.normalize_email(email), username=username, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, phone_number, email=None, password=None):
        if email==None:
            email = phone_number+"@gmail.com"
        user = self.create_user(phone_number, email, password, role="ADMIN")
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("USERS", "Users"),
        ("USER_KIN", "User Kin"),
        ("CARE_MANAGER", "Care Manager"),
        ("ADMIN", "Admin"),
        ("ENG_TEAM", "Engineering Team"),
    ]
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    username = models.CharField(max_length=50, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="USERS")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    objects = CustomUserManager()
    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []
    def __str__(self):
        return self.username
# Patient-related models
class Patient(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="patient_profile")
    dob = models.DateField(verbose_name="Date of Birth")
    full_name = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")])
    address = models.TextField(verbose_name="Address")
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    height = models.CharField(max_length=10)
    weight = models.CharField(max_length=10)
    id_proof_url = models.CharField(max_length=500, null=True, blank=True)
    profile_picture_url = models.CharField(max_length=500, null=True, blank=True)
    usual_wake_up_time = models.TimeField()
    current_location_status = models.CharField(max_length=50, choices=[('AtHome', 'At Home'), ('Travelling', 'Travelling')])
    expected_return_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    alternate_phone = models.CharField(max_length=15, blank=True)
    pin_code = models.CharField(max_length=15, blank=True)
    def __str__(self):
        return f"Patient Profile of {self.user.username}"
class EmergencyContacts(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="emergency_contacts")
    next_of_kin_name = models.CharField(max_length=100)
    next_of_kin_contact_number = models.CharField(max_length=15)
    relationship_with_senior = models.CharField(max_length=50)
    neighbor_name = models.CharField(max_length=100, null=True, blank=True)
    neighbor_contact_number = models.CharField(max_length=15, null=True, blank=True)

class MedicalHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="medical_histories")
    existing_health_conditions = models.TextField(null=True, blank=True, help_text="List any chronic illnesses")
    known_allergies = models.TextField(null=True, blank=True, help_text="Food, medication, environmental allergies")
    current_prescriptions_url = models.CharField(max_length=500, null=True, blank=True)
    past_surgeries = models.TextField(null=True, blank=True, help_text="Include dates if available")

class PreferredMedicalServices(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="preferred_medical_services")
    preferred_doctor_name = models.CharField(max_length=100, null=True, blank=True)
    doctor_contact_number = models.CharField(max_length=15, null=True, blank=True)
    preferred_hospital_or_clinic = models.CharField(max_length=100, null=True, blank=True)
    
class LifestyleDetails(models.Model):
    ACTIVITY_LEVEL_CHOICES = [
        ('Low', 'Low'),
        ('Moderate', 'Moderate'),
        ('High', 'High')
    ]
    DIET_PREFERENCES_CHOICES = [
        ('Vegetarian', 'Vegetarian'),
        ('Non-Vegetarian', 'Non-Vegetarian'),
        ('Vegan', 'Vegan'),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="lifestyle_details")
    activity_level = models.CharField(max_length=10, choices=ACTIVITY_LEVEL_CHOICES, null=True, blank=True)
    diet_preferences = models.CharField(max_length=15, choices=DIET_PREFERENCES_CHOICES, null=True, blank=True)
    requires_mobility_assistance = models.BooleanField(default=False)
    has_vision_impairment = models.BooleanField(default=False)
    has_hearing_impairment = models.BooleanField(default=False)


# New VitalSigns Model
class VitalSigns(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vital_signs')
    heart_rate = models.IntegerField()  # BPM
    blood_pressure = models.CharField(max_length=10)  # Example: 120/80 mmHg
    respiratory_rate = models.IntegerField()  # BPM
    temperature = models.FloatField()  # Celsius
    checked_at = models.DateTimeField(auto_now=True)

# New HealthMetrics Model
class HealthMetrics(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='health_metrics')
    blood_sugar = models.IntegerField(help_text='mg/dL')
    ecg = models.CharField(max_length=20, choices=[('Normal', 'Normal'), ('Abnormal', 'Abnormal')])
    bmi = models.FloatField()
    sleep_level = models.FloatField(help_text='Hours')
    stress_level = models.CharField(max_length=20, choices=[('Low', 'Low'), ('Moderate', 'Moderate'), ('High', 'High')])
    blood_oxygen = models.IntegerField(help_text='Percentage')
    checked_at = models.DateTimeField(auto_now=True)

# New CheckupSchedule Model
class CheckupSchedule(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='checkup_schedule')
    scheduled_date = models.DateField()
    status = models.CharField(max_length=20, choices=[('Scheduled', 'Scheduled'), ('Completed', 'Completed'), ('Missed', 'Missed')])

# New HealthStatusOverview Model
class HealthStatusOverview(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='health_status_overview')
    status_message = models.CharField(max_length=255, default='Your health metrics are within normal range')
    next_checkup_date = models.DateField()
