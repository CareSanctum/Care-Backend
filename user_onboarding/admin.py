from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser,
    Patient,
    EmergencyContacts,
    MedicalHistory,
    PreferredMedicalServices,
    LifestyleDetails,
    VitalSigns,
    HealthMetrics,
    CheckupSchedule,
    HealthStatusOverview
)

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("id", "username", "phone_number", "email", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "phone_number", "email")
    ordering = ("id",)

    fieldsets = (
        ("User Information", {"fields": ("phone_number", "email", "username", "role", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone_number", "email", "username", "role", "password1", "password2"),
        }),
    )

# Patient Admin
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "full_name", "dob", "gender", "phone", "blood_group")
    search_fields = ("full_name", "phone", "user__username")
    list_filter = ("gender", "blood_group")

# Emergency Contact Admin
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "next_of_kin_name", "next_of_kin_contact_number")
    search_fields = ("next_of_kin_name", "next_of_kin_contact_number", "patient__user__username")

# Medical History Admin
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "existing_health_conditions", "known_allergies")
    search_fields = ("patient__user__username", "existing_health_conditions")

# Preferred Medical Services Admin
class PreferredMedicalServicesAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "preferred_doctor_name", "preferred_hospital_or_clinic")
    search_fields = ("preferred_doctor_name", "preferred_hospital_or_clinic", "patient__user__username")

# Lifestyle Details Admin
class LifestyleDetailsAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "activity_level", "diet_preferences", "requires_mobility_assistance")
    search_fields = ("patient__user__username", "diet_preferences")
    list_filter = ("activity_level", "requires_mobility_assistance", "has_vision_impairment", "has_hearing_impairment")

# Vital Signs Admin
class VitalSignsAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "heart_rate", "blood_pressure", "respiratory_rate", "temperature", "checked_at")
    search_fields = ("patient__user__username",)
    list_filter = ("checked_at",)

# Health Metrics Admin
class HealthMetricsAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "blood_sugar", "ecg", "bmi", "sleep_level", "stress_level", "blood_oxygen", "checked_at")
    search_fields = ("patient__user__username",)
    list_filter = ("checked_at", "stress_level", "ecg")

# Checkup Schedule Admin
class CheckupScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "scheduled_date", "status")
    search_fields = ("patient__user__username",)
    list_filter = ("status", "scheduled_date")

# Health Status Overview Admin
class HealthStatusOverviewAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "status_message", "next_checkup_date")
    search_fields = ("patient__user__username", "status_message")
    list_filter = ("next_checkup_date",)

# Registering all models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(EmergencyContacts, EmergencyContactAdmin)
admin.site.register(MedicalHistory, MedicalHistoryAdmin)
admin.site.register(PreferredMedicalServices, PreferredMedicalServicesAdmin)
admin.site.register(LifestyleDetails, LifestyleDetailsAdmin)
admin.site.register(VitalSigns, VitalSignsAdmin)
admin.site.register(HealthMetrics, HealthMetricsAdmin)
admin.site.register(CheckupSchedule, CheckupScheduleAdmin)
admin.site.register(HealthStatusOverview, HealthStatusOverviewAdmin)
