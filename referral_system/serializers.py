from rest_framework import serializers
from .models import *
from user_onboarding.serializers import CustomUserSerializer

class ReferralCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralCode
        fields = "__all__"

class LeadSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    class Meta:
        model = Lead
        fields = "__all__"

class CommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commission
        fields = "__all__"
