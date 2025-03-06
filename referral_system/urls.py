from django.urls import path
from .views import *

urlpatterns = [
    path("b2c-code/", send_b2c_code, name="get-b2c-code"),
    path("b2b-code/", send_b2b_code, name="get-b2b-code"),
    path("create-lead/", create_lead, name="create-lead"),
    path("create-commission/", create_commission, name="create-commission"),
    path("get-leads/", get_leads_and_commissions, name="get-leads"),
]