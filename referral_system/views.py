from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from rest_framework.decorators import api_view

# Create your views here.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import B2BPartner, B2CUser, ReferralCode, Lead

#get all the converted leads for a user or a b2b partner
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
        if username and company_name:
            return Response(
                {"error": "Please provide either a username or a company_name, not both."},
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
    
#gets all the leads that have been referred by a user or a b2b partner(not necessarily a lead that has been converted)
class ReferredLeadsAPIView(APIView):
    def get(self, request):
        # Get the query parameter (username or company_name)
        username = request.query_params.get('username', None)
        company_name = request.query_params.get('company_name', None)

        if not username and not company_name:
            return Response(
                {"error": "Please provide either a username or a company_name."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if username and company_name:
            return Response(
                {"error": "Please provide either a username or a company_name, not both."},
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
        converted_leads = Lead.objects.filter(referred_through=referral_code)

        # Prepare the response data

        return Response({"converted_leads": converted_leads}, status=status.HTTP_200_OK)

def create_link(code):
    return f"https://webapp.caresanctum.com/signup?referral_code={code}"

#get the referral code and link for a b2c user
@api_view(['POST'])
def send_b2c_code(request):
    username = request.data.get('username')
    b2c_obj = B2CUser.objects.get(user__username=username)
    referral_code = ReferralCode.objects.get(b2c_user=b2c_obj)
    code = referral_code.code
    link = create_link(code)
    return Response({"code": code, "link": link}, status=status.HTTP_200_OK)

#get the referral code and link for a b2b partner
@api_view(['POST'])
def send_b2b_code(request):
    company_name = request.data.get('company_name')
    b2b_obj = B2BPartner.objects.get(company_name=company_name)
    referral_code = ReferralCode.objects.get(b2b_partner=b2b_obj)
    code = referral_code.code
    link = create_link(code)
    return Response({"code": code, "link": link}, status=status.HTTP_200_OK)


#create a commission object whenever a lead is converted 
@api_view(['POST'])
def create_commission(request):
    data = request.data
    username = data.get('username')
    bought_service_cost = data.get('bought_service_cost')

    if not username and not bought_service_cost:
        return Response(
            {"error": "Please provide both username and bought_service_cost."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = CustomUser.objects.get(username=username)
        lead = Lead.objects.get(user=user)

        referral = lead.referred_through

        if not referral:
            return Response({"error": "This user was not referred through a valid referral code"}, status=status.HTTP_400_BAD_REQUEST)
        
        b2b_receipent = None
        b2c_receipent = None
        commission_percentage = 0

        if referral.type == "B2B_PARTNER":
            b2b_receipent = referral.b2b_partner
            commission_percentage = B2B_COMMISSION_PERCENTAGE
        elif referral.type == "B2C_USER":
            b2c_receipent = referral.b2c_user
            commission_percentage = B2C_COMMISSION_PERCENTAGE

        commission = Commission.objects.create(
            lead=lead,
            status = "IN_PROCESS",
            percentage=commission_percentage,
            amount=(commission_percentage/100) * bought_service_cost,
            b2b_receipent=b2b_receipent,
            b2c_receipent=b2c_receipent
        )
        lead.converted = True
        return Response(CommissionSerializer(commission).data, status=status.HTTP_201_CREATED)
    
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Lead.DoesNotExist:
        return Response({"error": "Lead not found for this user"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

#creates a lead object when they put a referral code
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



#gets all the leads and commissions associated with a referral code
@api_view(["GET"])
def get_leads_and_commissions(request):
    referral_code = request.data.get("referral_code")
    try:
        # Find the referral code object
        referral = ReferralCode.objects.get(code=referral_code)

        # Find all leads associated with this referral code
        leads = Lead.objects.filter(referred_through=referral)

        # Prepare the response data
        leads_data = []
        for lead in leads:
            # Check if a commission exists for this lead
            commission = Commission.objects.filter(lead=lead).first()

            leads_data.append({
                "lead": LeadSerializer(lead).data,
                "commission": CommissionSerializer(commission).data if commission else None
            })

        return Response(leads_data, status=status.HTTP_200_OK)

    except ReferralCode.DoesNotExist:
        return Response({"error": "Referral code not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
