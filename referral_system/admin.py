from django.contrib import admin
from .models import *

# Register your models here.

class B2BPatnerAdmin(admin.ModelAdmin):
    list_display = ("id", "company_name", "registered_by")
    search_fields = ("company_name", "registered_by__username")
    list_filter = ("company_name", "registered_by__username")

class B2CUserAdmin(admin.ModelAdmin):
    list_display = ("id", "user")
    search_fields = ("user__username",)
    list_filter = ("user__username",)

class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "b2b_partner", "b2c_user", "code")
    search_fields = ("code",)
    list_filter = ("type",)

class LeadAdmin(admin.ModelAdmin):
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

class CommissionAdmin(admin.ModelAdmin):
    list_display = ("id", "b2b_receipent", "b2c_receipent", "amount", "status")
    search_fields = ("b2b_partner__company_name", "b2c_user__user__username")
    list_filter = ("status",)

admin.site.register(B2BPartner, B2BPatnerAdmin)
admin.site.register(B2CUser, B2CUserAdmin)
admin.site.register(ReferralCode, ReferralCodeAdmin)
admin.site.register(Lead, LeadAdmin)
admin.site.register(Commission, CommissionAdmin)
