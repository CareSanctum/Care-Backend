from django.urls import path
from .views import *
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("add_patient_data/", CreateOrUpdatePatientData.as_view(), name="add_patient_data"),
    path("user-details/<str:username>/", UserDetailsView.as_view(), name="user-details"),
     path("upload-file/", FileUploadAPIView.as_view(), name="upload-file"),
     path('health-data/<str:username>', get_patient_health_data, name='get_patient_health_data'),
    path('health-data/update/<str:username>', create_or_update_health_data, name='create_or_update_health_data'),
    path('patient-usernames/', PatientUsernamesListView.as_view(), name='patient-usernames-list'),
]