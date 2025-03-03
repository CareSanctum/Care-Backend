from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import *
from rest_framework.decorators import api_view

# Create your views here.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import B2BPartner, B2CUser, ReferralCode, Lead

class ConvertedLeadsAPIView(APIView):
    def get(self, request):
        # Get the query parameter (username or company_name)
        username = request.query_params.get('username', None)
        company_name = request.query_params.get('company_name', None)

        if not username and not company_name:
            return Response(
                {"error": "Please provide either a username or a company_name."},
                status=status.HTTP_400_BAD_REQUEST
            )

        referral_code = None

        # Check if the request is for a B2CUser
        if username:
            b2c_user = get_object_or_404(B2CUser, user__username=username)
            referral_code = ReferralCode.objects.filter(b2c_user=b2c_user).first()

        # Check if the request is for a B2BPartner
        elif company_name:
            b2b_partner = get_object_or_404(B2BPartner, company_name=company_name)
            referral_code = ReferralCode.objects.filter(b2b_partner=b2b_partner).first()

        # If no referral code is found, return an empty list
        if not referral_code:
            return Response(
                {"error": "No referral code found for the provided username or company_name."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Fetch all converted leads for the referral code
        converted_leads = Lead.objects.filter(referred_through=referral_code, converted=True)

        # Prepare the response data

        return Response({"converted_leads": converted_leads}, status=status.HTTP_200_OK)
    
@api_view(['POST'])
def create_lead(request):
    username = request.data.get("username")
    referral_code = request.data.get("referral_code")

    code_obj = ReferralCode.objects.get(code=referral_code)

    if code_obj is None:
        return Response(
            {"error": "Invalid referral code."},
            status=status.HTTP_400_BAD_REQUEST
        )
    Lead.objects.create(
        user=CustomUser.objects.get(username=username),
        referred_through=code_obj,
        converted = False
    )
    return Response(
        {"message": "Lead created successfully."},
        status=status.HTTP_201_CREATED
    )

