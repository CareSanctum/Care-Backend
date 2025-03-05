from django.urls import path
from .views import *

urlpatterns = [
    path("referrals/converted-leads/", ConvertedLeadsAPIView.as_view(), name="converted-leads"),
    path("referrals/b2c-code/", send_b2c_code, name="get-b2c-code"),
    path("referrals/b2b-code/", send_b2b_code, name="get-b2b-code"),
]