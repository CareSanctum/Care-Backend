from django.urls import path
from .views import *

urlpatterns = [
    path("referrals/converted-leads/", ConvertedLeadsAPIView.as_view(), name="converted-leads"),
    path("referrals/create-lead/", create_lead, name="create-lead"),
]