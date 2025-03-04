from rest_framework import serializers
from .models import *

class ReferralCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralCode
        fields = "__all__"

class LeadSerializer(serializers.ModelSerializer):
    referred_through = ReferralCodeSerializer()
    class Meta:
        model = Lead
        fields = "__all__"

class CommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commission
        fields = "__all__"
