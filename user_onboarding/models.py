from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group
from django.db import models
import uuid
from django.utils.timezone import now

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
    care_manager = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_patient", limit_choices_to={'role': 'CARE_MANAGER'})
    admin = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="admin_patient", limit_choices_to={'role': 'ADMIN'})
    kin = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="kin_patient", limit_choices_to={'role': 'USER_KIN'})
    dob = models.DateField(verbose_name="Date of Birth",null = True, blank=True)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")], null = True, blank=True)
    address = models.TextField(verbose_name="Address", null = True, blank=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, null = True, blank=True)
    height = models.CharField(max_length=10, null = True, blank=True)
    weight = models.CharField(max_length=10, null = True, blank=True)
    id_proof_url = models.CharField(max_length=500, null=True, blank=True)
    profile_picture_url = models.CharField(max_length=500, null=True, blank=True)
    usual_wake_up_time = models.TimeField(null = True, blank=True)
    current_location_status = models.CharField(max_length=50, null = True, blank=True, choices=[('AtHome', 'At Home'), ('Travelling', 'Travelling')])
    expected_return_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null = True)
    alternate_phone = models.CharField(max_length=15, blank=True, null = True)
    pin_code = models.CharField(max_length=15, blank=True, null = True)
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


class Ticket(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
    ]

    REMARK_CHOICES = [
        ("ESCALATED_TO_ADMIN", "Escalated to Admin"),
        ("ESCALATED_TO_CARE_TEAM", "Escalated to Care Team"),
        ("ESCALATED_TO_KIN", "Escalated to Kin"),
    ]

    ticket_number = models.CharField(max_length=100, unique=True, editable=False)
    user_initiated = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="initiated_tickets")
    user_assigned = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tickets")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    remark = models.CharField(max_length=50, choices=REMARK_CHOICES, null=True, blank=True)
    description = models.TextField()
    date_initiated = models.DateTimeField(default=now)
    date_closed = models.DateTimeField(null=True, blank=True)
    service_name = models.CharField(max_length=100)
    current_work = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            unique_id = uuid.uuid4().hex[:6].upper()
            self.ticket_number = f"{self.user_initiated.username}_{unique_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.status}"




from django.contrib.auth import get_user_model

User = get_user_model()

class ScheduledVisit(models.Model):
    VISIT_TYPES = [
        ('care_manager', 'Care Manager'),
        ('buddy', 'Buddy'),
        ('doctor', 'Doctor'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('rescheduled', 'Rescheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='scheduled_visits')
    visit_type = models.CharField(max_length=20, choices=VISIT_TYPES)
    scheduled_datetime = models.DateTimeField(default=now,null = True)
    gmeet_link = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.visit_type} visit for {self.patient.user.username} on {self.scheduled_datetime}"



class CommunityEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, null=True)
    registered_users = models.ManyToManyField(CustomUser, related_name="community_events", blank=True)
    total_registered = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        """Save the event first before updating total_registered"""
        is_new = self.pk is None  # Check if it's a new event
        super().save(*args, **kwargs)  # Save the instance first

        if not is_new:  # Only update if it's an existing object
            self.total_registered = self.registered_users.count()
            super().save(update_fields=["total_registered"])

    def __str__(self):
        return self.name


class CurrentMedication(models.Model):
    STATUS_CHOICES = [
        ("current", "Current"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="medications")
    medicine_name = models.CharField(max_length=255, blank=True, null=True)
    dosage = models.CharField(max_length=100, blank=True, null=True)
    timing = models.CharField(max_length=100, blank=True, null=True)
    prescribed_by = models.CharField(max_length=255, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    stock_remaining = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="current")

    def is_expired(self):
        """Check if the medicine is expired."""
        return self.expiry_date and self.expiry_date < now().date()

    def __str__(self):
        return f"{self.medicine_name} - {self.user.username}" if self.medicine_name else f"Medication for {self.user.username}"
    
  


class Prescription(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="prescriptions")
    Presc_file_url = models.URLField()
    doctor_name = models.CharField(max_length=255)
    prescribed_date = models.DateField()

    def __str__(self):
        return f"Prescription by {self.doctor_name} on {self.prescribed_date}"

class LabReport(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="lab_reports")
    test_name = models.CharField(max_length=255)
    test_date = models.DateField()
    LR_file_url = models.URLField()

    def __str__(self):
        return f"Lab Report: {self.test_name} on {self.test_date}"