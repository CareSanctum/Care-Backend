from django.urls import path
from .views import *

urlpatterns = [
    path("b2c-code/", send_b2c_code, name="get-b2c-code"),
    path("b2b-code/", send_b2b_details, name="get-b2b-code"),
    path("create-lead/", create_lead, name="create-lead"),
    path("get-lead/", getLeadDetails, name="get-lead"),
    path("create-commission/", create_commission, name="create-commission"),
    path("get-leads/", get_leads_and_commissions, name="get-leads"),
    path("get-b2c-referral-stats/", get_b2c_referral_stats, name="get-b2c-referral-stats"),
    path("get-b2b-referral-stats/", get_b2b_referral_stats, name="get-b2b-referral-stats"),
    path("ranked-b2c-users/", ranked_b2c_users_by_commission, name="ranked-b2c-users"),
]