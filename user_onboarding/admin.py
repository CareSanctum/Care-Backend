from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *
from referral_system.models import *

# ✅ Custom AdminSite
class CustomAdminSite(admin.AdminSite):
    site_header = "CareSanctum Admin"
    site_title = "CareSanctum Portal"
    index_title = "Welcome to CareSanctum Admin"

    def has_permission(self, request):
        return request.user.is_active and request.user.is_staff

custom_admin_site = CustomAdminSite(name='custom_admin')

# ✅ Custom User Admin
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

# ✅ Shared Restriction Mixin for hiding models from CARE_MANAGER
class HideFromCareManagerMixin:
    def has_module_permission(self, request):
        return request.user.role != "CARE_MANAGER"

    def has_view_permission(self, request, obj=None):
        return request.user.role != "CARE_MANAGER"

# ✅ ModelAdmin Classes

class PatientAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "user", "full_name", "dob", "gender", "phone", "blood_group")
    search_fields = ("full_name", "phone", "user__username")
    list_filter = ("gender", "blood_group")

    def has_module_permission(self, request):
        return request.user.role == "CARE_MANAGER" or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.role == "CARE_MANAGER" or request.user.is_superuser

class EmergencyContactAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "patient", "next_of_kin_name", "next_of_kin_contact_number")
    search_fields = ("next_of_kin_name", "next_of_kin_contact_number", "patient__user__username")

class MedicalHistoryAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "patient", "existing_health_conditions", "known_allergies")
    search_fields = ("patient__user__username", "existing_health_conditions")

class PreferredMedicalServicesAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "patient", "preferred_doctor_name", "preferred_hospital_or_clinic")
    search_fields = ("preferred_doctor_name", "preferred_hospital_or_clinic", "patient__user__username")

class LifestyleDetailsAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "patient", "activity_level", "diet_preferences", "requires_mobility_assistance")
    search_fields = ("patient__user__username", "diet_preferences")
    list_filter = ("activity_level", "requires_mobility_assistance", "has_vision_impairment", "has_hearing_impairment")

class VitalSignsAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "patient", "heart_rate", "blood_pressure", "respiratory_rate", "temperature", "checked_at")
    search_fields = ("patient__user__username",)
    list_filter = ("checked_at",)

class HealthMetricsAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "patient", "blood_sugar", "ecg", "bmi", "sleep_level", "stress_level", "blood_oxygen", "checked_at")
    search_fields = ("patient__user__username",)
    list_filter = ("checked_at", "stress_level", "ecg")

class CheckupScheduleAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "patient", "scheduled_date", "status")
    search_fields = ("patient__user__username",)
    list_filter = ("status", "scheduled_date")

class HealthStatusOverviewAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "patient", "status_message", "next_checkup_date")
    search_fields = ("patient__user__username", "status_message")
    list_filter = ("next_checkup_date",)

class TicketAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("ticket_number", "user_initiated", "user_assigned", "status", "service_name", "date_initiated", "date_closed")
    list_filter = ("status", "service_name", "date_initiated")
    search_fields = ("ticket_number", "user_initiated__username", "user_assigned__username", "service_name")
    readonly_fields = ("ticket_number", "date_initiated", "date_closed")

    def save_model(self, request, obj, form, change):
        if not obj.ticket_number:
            obj.save()
        super().save_model(request, obj, form, change)

class ScheduledVisitAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "patient", "visit_type", "status")
    list_filter = ("visit_type", "status")
    search_fields = ("patient__username", "visit_type")

class CommunityEventAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "name", "date", "total_registered")
    search_fields = ("id",)
    ordering = ("date",)

class CurrentMedicationAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("medicine_name", "user", "dosage", "timing", "prescribed_by", "expiry_date", "stock_remaining", "status")
    search_fields = ("medicine_name", "user__username", "prescribed_by")
    list_filter = ("status", "expiry_date")

class PrescriptionAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("prescribed_date", "doctor_name", "Presc_file_url")
    search_fields = ("user__username",)

class LabReportAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("test_date", "test_name", "LR_file_url")
    search_fields = ("user__username",)

class UserDeviceAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ["user", "name", "device_code"]
    list_filter = ["user"]

    def has_module_permission(self, request):
        return request.user.role == "CARE_MANAGER" or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.role == "CARE_MANAGER" or request.user.is_superuser

from django.contrib import admin
from .models import IngestionData
from .forms import IngestionDataForm


class IngestionDataAdmin(admin.ModelAdmin):
    form = IngestionDataForm

    list_display = [
        "user", "device", "get_heart_rate", "get_blood_oxygen", "source", "status", "created_at"
    ]
    list_filter = ["device", "status"]
    search_fields = ["user__username", "device__device_code", "source"]

    readonly_fields = ["created_at", "created_by"]

    def get_heart_rate(self, obj):
        return obj.data.get("heart_rate") if obj.data else None
    get_heart_rate.short_description = "Heart Rate (BPM)"

    def get_blood_oxygen(self, obj):
        return obj.data.get("blood_oxygen") if obj.data else None
    get_blood_oxygen.short_description = "Blood Oxygen (%)"

    def has_module_permission(self, request):
        return request.user.role == "CARE_MANAGER" or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.role == "CARE_MANAGER" or request.user.is_superuser

    def get_form(self, request, obj=None, **kwargs):
        # Inject request into the form for dynamic behavior
        form = super().get_form(request, obj, **kwargs)
        form.request = request
        return form

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


custom_admin_site.register(IngestionData, IngestionDataAdmin)


custom_admin_site.register(CustomUser, CustomUserAdmin)
custom_admin_site.register(Patient, PatientAdmin)
custom_admin_site.register(CurrentMedication, CurrentMedicationAdmin)
custom_admin_site.register(ScheduledVisit, ScheduledVisitAdmin)
custom_admin_site.register(CommunityEvent, CommunityEventAdmin)
custom_admin_site.register(Ticket, TicketAdmin)
custom_admin_site.register(EmergencyContacts, EmergencyContactAdmin)
custom_admin_site.register(MedicalHistory, MedicalHistoryAdmin)
custom_admin_site.register(PreferredMedicalServices, PreferredMedicalServicesAdmin)
custom_admin_site.register(LifestyleDetails, LifestyleDetailsAdmin)
custom_admin_site.register(VitalSigns, VitalSignsAdmin)
custom_admin_site.register(HealthMetrics, HealthMetricsAdmin)
custom_admin_site.register(CheckupSchedule, CheckupScheduleAdmin)
custom_admin_site.register(HealthStatusOverview, HealthStatusOverviewAdmin)
custom_admin_site.register(Prescription, PrescriptionAdmin)
custom_admin_site.register(LabReport, LabReportAdmin)
custom_admin_site.register(UserDevice, UserDeviceAdmin)





# Register your models here.

class B2BPatnerAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "company_name", "registered_by")
    search_fields = ("company_name", "registered_by__username")
    list_filter = ("company_name", "registered_by__username")

class B2CUserAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "user")
    search_fields = ("user__username",)
    list_filter = ("user__username",)

class ReferralCodeAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "type", "b2b_partner", "b2c_user", "code")
    search_fields = ("code",)
    list_filter = ("type",)

class LeadAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "get_user_username", "get_referred_through_code")
    search_fields = ("user__username", "referred_through__code")
    list_filter = ("referred_through__code",)

    #returns username of the lead
    def get_user_username(self, obj): 
        return obj.user.username
    get_user_username.short_description = "Username"  # Column header

    #returns the code Lead used to register
    def get_referred_through_code(self, obj):
        return obj.referred_through.code
    
    get_referred_through_code.short_description = "Referred Through Code" # Column header

class CommissionAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "b2b_receipent", "b2c_receipent", "amount", "status")
    search_fields = ("b2b_partner__company_name", "b2c_user__user__username")
    list_filter = ("status",)

class CommissionPercentageAdmin(HideFromCareManagerMixin, admin.ModelAdmin):
    list_display = ("id", "b2b_commission_percentage", "b2c_commission_percentage")

custom_admin_site.register(B2BPartner, B2BPatnerAdmin)
custom_admin_site.register(B2CUser, B2CUserAdmin)
custom_admin_site.register(ReferralCode, ReferralCodeAdmin)
custom_admin_site.register(Lead, LeadAdmin)
custom_admin_site.register(Commission, CommissionAdmin)
custom_admin_site.register(CommissionPercentage, CommissionPercentageAdmin)