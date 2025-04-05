from django.urls import path
from .views import *
from .admin import custom_admin_site
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("add-patient-data/", CreateOrUpdatePatientData.as_view(), name="add_patient_data"),
    path("user-details/<str:username>/", UserDetailsView.as_view(), name="user_details"),
    path("upload-file/", FileUploadAPIView.as_view(), name="upload-file"),
    path('health-data/<str:username>/', get_patient_health_data, name='get_patient_health_data'),
    path('health-data/update/<str:username>/', create_or_update_health_data, name='create_or_update_health_data'),
    path('patient-usernames/', PatientUsernamesListView.as_view(), name='patient_usernames_list'),
    path("create-ticket/", CreateTicketForCareManagerView.as_view(), name="create_ticket"),
    path("tickets/", get_tickets, name="get-tickets"),
    path("schedule-visit/", ScheduleVisitAPIView.as_view(), name="schedule-visit"),
    path("get-schedules/<str:username>/", GetPatientSchedulesAPIView.as_view(), name="get-schedules"),
    path("latest-events/", latest_community_events, name="latest-events"),
    path("register-event/", register_for_event, name="register-event"),
    path('medications/upload-document/', MedicationViewSet.as_view({'post': 'upload_document'}), name='upload-document'),
    path('medications/get-medications/', MedicationViewSet.as_view({'get': 'get_medications'}), name='get-medications'),
    path("patient/<str:username>/", get_patient_details, name="get_patient_details"),
    path("contact-CM/", contact_CM, name="contact-CareManager"),
    path("lab-reports/<str:username>/", get_lab_reports, name="get_lab_reports"),
    path("prescriptions/<str:username>/", get_prescriptions, name="get_prescriptions"),
    path("get-assigned-users/<str:care_manager_username>/",AssignedPatientsView.as_view() , name ="get_assigned_care_managers"),
    path("assign/", AssignRolesView.as_view(), name="assign"),
    path("create-admin/", create_admin_user, name="create-admin"),
    path("admin/", custom_admin_site.urls),
]