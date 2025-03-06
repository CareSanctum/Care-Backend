from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from rest_framework.decorators import api_view
from decimal import Decimal

# Create your views here.

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
    bought_service_cost = Decimal(data.get('bought_service_cost'))

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
        commission_settings = CommissionPercentage.objects.first()

        if referral.type == "B2B_PARTNER":
            b2b_receipent = referral.b2b_partner
            commission_percentage = commission_settings.b2b_commission_percentage
        elif referral.type == "B2C_USER":
            b2c_receipent = referral.b2c_user
            commission_percentage = commission_settings.b2c_commission_percentage

        commission = Commission.objects.create(
            lead=lead,
            status = "IN_PROCESS",
            percentage=commission_percentage,
            amount= ((commission_percentage/100) * bought_service_cost),
            b2b_receipent=b2b_receipent,
            b2c_receipent=b2c_receipent
        )
        lead.converted = True
        lead.save()
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

    try:
        user = CustomUser.objects.get(username=username)
        code_obj = ReferralCode.objects.get(code=referral_code)
    except (CustomUser.DoesNotExist, ReferralCode.DoesNotExist):
        return Response(
            {"error": "Invalid username or referral code."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if Lead.objects.filter(user=user).exists():
        return Response({"error": "Lead already exists for this user"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        Lead.objects.create(
            user=CustomUser.objects.get(username=username),
            referred_through=code_obj,
            converted = False
        )
        return Response(
            {"message": "Lead created successfully."},
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#gets all the leads and commissions associated with a referral code
@api_view(["GET"])
def get_leads_and_commissions(request):
    referral_code = request.GET.get("referral_code")
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
