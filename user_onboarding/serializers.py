from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *

CustomUser = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, min_length=6) #added a confirm password field while registration
    class Meta:
        model = CustomUser
        fields = ["email", "phone_number", "password", "confirm_password"]
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 6},
        }

    def validate(self, data):
        if not data.get("email") and not data.get("phone_number"):
            raise serializers.ValidationError("Either email or phone number is required.")
        if data["password"] != data["confirm_password"]: #validate confirm_password and password
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password") #remove confirm_password before saving
        user = CustomUser.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()  # Can be email or phone number
    password = serializers.CharField(write_only=True)

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContacts
        fields = '__all__'

class MedicalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalHistory
        fields = '__all__'

class PreferredMedicalServicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferredMedicalServices
        fields = '__all__'

class LifestyleDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LifestyleDetails
        fields = '__all__'
