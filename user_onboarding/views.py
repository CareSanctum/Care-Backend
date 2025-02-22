from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import requests
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
import boto3
from care_app import settings
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.utils.timezone import now
from django.core.mail import send_mail
# Initialize S3 client using Django settings
s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
)
# Get S3 bucket name from settings
BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # ✅ Ensure a Patient object is created for USERS role
        #changes made here (before two create functions were there the second one used to overwrite the first one now both of them are merged)
        if user.role == "USERS":
            Patient.objects.create(
                user=user,
                dob=None,
                full_name=user.username,  # Default full_name to username
                gender=None,
                address="",
                blood_group=None,
                height="",
                weight="",
                id_proof_url="",
                profile_picture_url="",
                usual_wake_up_time=None,
                current_location_status='AtHome',
                expected_return_date=None,
                phone=user.phone_number,
                alternate_phone="",
                pin_code=""
            )

        # ✅ Generate JWT tokens
        token = RefreshToken.for_user(user)
        return Response({
            "refresh": str(token),
            "access": str(token.access_token),
            "user_name": str(user.username)
        }, status=status.HTTP_201_CREATED)
    
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data.get("identifier")  # Email or phone
        password = serializer.validated_data.get("password")

        # Find user by email or phone number
        user = CustomUser.objects.filter(email=identifier).first() or CustomUser.objects.filter(phone_number=identifier).first()

        if user is None or not user.check_password(password):
            return Response({"error": "Invalid email/phone number or password"}, status=status.HTTP_401_UNAUTHORIZED)

        token = RefreshToken.for_user(user)
        return Response({
            "refresh": str(token),
            "access": str(token.access_token),
            "user_name" : str(user.username)
        }, status=status.HTTP_200_OK)


class CreateOrUpdatePatientData(APIView):
    def post(self, request):
        username = request.data.get("username")
        if not username:
            return Response({"error": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Get user
        user = get_object_or_404(CustomUser, username=username)

        # 1. Patient (Handling File Upload for id_proof)
        patient_data = request.data.get("patient", {})
        if "id_proof" in request.FILES:  # Check if file is uploaded
            patient_data["id_proof"] = request.FILES["id_proof"]

        if "profile_picture" in request.FILES:  # Check if file is uploaded
            patient_data["profile_picture"] = request.FILES["profile_picture"]

        patient, _ = Patient.objects.update_or_create(
            user=user,
            defaults=patient_data
        )

        # 2. Emergency Contacts
        emergency_contacts_data = request.data.get("emergency_contacts", {})
        EmergencyContacts.objects.update_or_create(
            patient=patient,
            defaults=emergency_contacts_data
        )
            

        # 3. Medical History (Handling File Upload for current_prescriptions)
        medical_history_data = request.data.get("medical_history", {})
        if "current_prescriptions" in request.FILES:  # Check if file is uploaded
            medical_history_data["current_prescriptions"] = request.FILES["current_prescriptions"]

        MedicalHistory.objects.update_or_create(
            patient=patient,
            defaults=medical_history_data
        )

        # 4. Preferred Medical Services
        preferred_services_data = request.data.get("preferred_medical_services", {})
        PreferredMedicalServices.objects.update_or_create(
            patient=patient,
            defaults=preferred_services_data
        )

        # 5. Lifestyle Details
        lifestyle_details_data = request.data.get("lifestyle_details", {})
        LifestyleDetails.objects.update_or_create(
            patient=patient,
            defaults=lifestyle_details_data
        )

        return Response({"message": "Records successfully added/updated"}, status=status.HTTP_201_CREATED)

# Allowed file fields per model
ALLOWED_FIELDS = {
    "Patient": {
        "id_proof": "id_proof_url",
        "profile_picture": "profile_picture_url",
    },
    "MedicalHistory": {
        "current_prescriptions": "current_prescriptions_url",
    },
}

class FileUploadAPIView(APIView):
    parser_classes = [MultiPartParser]
    def post(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        field_name = request.data.get("name")  # e.g., "id_proof" or "current_prescriptions"
        user_name = request.data.get("user_name")  # Required for both models
        if not file or not field_name or not user_name:
            return Response({"error": "Missing required parameters"}, status=status.HTTP_400_BAD_REQUEST)
        # Determine target model
        model = None
        if field_name in ALLOWED_FIELDS["Patient"]:
            model = Patient
        elif field_name in ALLOWED_FIELDS["MedicalHistory"]:
            model = MedicalHistory
        else:
            return Response({"error": "Invalid field name"}, status=status.HTTP_400_BAD_REQUEST)
        # Get the correct instance (Patient or MedicalHistory)
        instance = None
        if model == Patient:
            instance = get_object_or_404(Patient, user__username=user_name)
            folder = f"patients/{user_name}"
            model_name = "Patient"
        elif model == MedicalHistory:
            instance = get_object_or_404(MedicalHistory, patient__user__username=user_name)  # Fetch medical history for the patient
            folder = f"medical_history/{user_name}"
            model_name = "MedicalHistory"
        # Define correct field
        field_to_update = ALLOWED_FIELDS[model_name].get(field_name)
        if not field_to_update:
            return Response({"error": "Invalid field mapping"}, status=status.HTTP_400_BAD_REQUEST)
        # Define file path in S3
        s3_path = f"{folder}/{field_name}/{file.name}"
        try:
            # Upload file to S3
            s3.upload_fileobj(file, BUCKET_NAME, s3_path, ExtraArgs={'ACL': 'public-read'})
            # Generate public file URL
            file_url = f"https://{BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_path}"
            # Update the model field with the S3 URL
            setattr(instance, field_to_update, file_url)
            instance.save()
            return Response({"message": "File uploaded successfully", "file_url": file_url}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailsView(APIView):
    """
    API to fetch all user details based on the username.
    """
    def get(self, request, username):
        # Fetch User
        user = get_object_or_404(CustomUser, username=username)
        
        # Fetch Related Data
        patient = Patient.objects.filter(user=user).first()
        emergency_contacts = EmergencyContacts.objects.filter(patient=patient).first()
        medical_history = MedicalHistory.objects.filter(patient=patient).first()
        preferred_services = PreferredMedicalServices.objects.filter(patient=patient).first()
        lifestyle_details = LifestyleDetails.objects.filter(patient=patient).first()
        
        # Serialize Data
        response_data = {
            "username": user.username,
            "patient": PatientSerializer(patient).data if patient else None,
            "emergency_contacts": EmergencyContactSerializer(emergency_contacts).data if emergency_contacts else None,
            "medical_history": MedicalHistorySerializer(medical_history).data if medical_history else None,
            "preferred_medical_services": PreferredMedicalServicesSerializer(preferred_services).data if preferred_services else None,
            "lifestyle_details": LifestyleDetailsSerializer(lifestyle_details).data if lifestyle_details else None
        }

        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_patient_health_data(request, username):
    try:
        # Fetch patient linked to user_id
        patient = Patient.objects.get(user__username=username)
        
        # Get the latest records for each model
        vital_signs = VitalSigns.objects.filter(patient=patient).order_by('-checked_at').first()
        health_metrics = HealthMetrics.objects.filter(patient=patient).order_by('-checked_at').first()
        checkup_schedule = CheckupSchedule.objects.filter(patient=patient).order_by('-scheduled_date').first()
        health_status = HealthStatusOverview.objects.filter(patient=patient).first()

        # Prepare response JSON
        data = {
            "user_id": username,
            "vital_signs": VitalSignsSerializer(vital_signs).data if vital_signs else None,
            "health_metrics": HealthMetricsSerializer(health_metrics).data if health_metrics else None,
            "checkup_schedule": CheckupScheduleSerializer(checkup_schedule).data if checkup_schedule else None,
            "health_status_overview": HealthStatusOverviewSerializer(health_status).data if health_status else None,
        }

        return Response(data, status=status.HTTP_200_OK)

    except Patient.DoesNotExist:
        return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def create_or_update_health_data(request, username):
    try:
        patient = Patient.objects.get(user__username=username)
    except Patient.DoesNotExist:
        return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = PatientHealthDataSerializer(data=request.data, partial=True)
    
    if serializer.is_valid():
        with transaction.atomic():  # Ensure atomicity
            validated_data = serializer.validated_data

            # Update only provided fields
            if "vital_signs" in validated_data:
                VitalSigns.objects.update_or_create(
                    patient=patient,
                    defaults=validated_data["vital_signs"]
                )

            if "health_metrics" in validated_data:
                HealthMetrics.objects.update_or_create(
                    patient=patient,
                    defaults=validated_data["health_metrics"]
                )

            if "checkup_schedule" in validated_data:
                CheckupSchedule.objects.update_or_create(
                    patient=patient,
                    defaults=validated_data["checkup_schedule"]
                )

            if "health_status_overview" in validated_data:
                HealthStatusOverview.objects.update_or_create(
                    patient=patient,
                    defaults=validated_data["health_status_overview"]
                )

        return Response({"message": "Health data updated successfully"}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientUsernamesListView(APIView):
    def get(self, request):
        usernames = Patient.objects.values_list("user__username", flat=True)  # Fetch only usernames
        return Response({"usernames": list(usernames)})


class AssignRolesView(generics.UpdateAPIView):
    def put(self, request, *args, **kwargs):
        patient_username = request.data.get("patient_username")
        care_manager_username = request.data.get("care_manager_username")
        admin_username = request.data.get("admin_username")
        kin_username = request.data.get("kin_username")

        user_obj = get_object_or_404(CustomUser, username = patient_username)
        patient, created = Patient.objects.update_or_create(user = user_obj, defaults={
            "full_name" : patient_username
        } )
        

        if care_manager_username:
            patient.care_manager = get_object_or_404(CustomUser, username=care_manager_username, role="CARE_MANAGER")
        if admin_username:
            patient.admin = get_object_or_404(CustomUser, username = admin_username, role="ADMIN")
        if kin_username:
            patient.kin = get_object_or_404(CustomUser, username = kin_username, role="USER_KIN")

        patient.save()
        return Response({"message": "Roles assigned successfully."}, status=status.HTTP_200_OK)
    

def create_or_update_ticket(ticket_id=None, **fields):
    if ticket_id:
        ticket = Ticket.objects.filter(id=ticket_id).first()
        if not ticket:
            return {"error": "Ticket not found"}
    else:
        ticket = Ticket()

    for field, value in fields.items():
        setattr(ticket, field, value)

    # Auto-set date_closed if status changes to CLOSED
    if "status" in fields and fields["status"] == "CLOSED":
        ticket.date_closed = now()

    ticket.save()
    return {"message": "Service requested successfully", "ticket_number": ticket.ticket_number}


class CreateTicketForCareManagerView(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        service_name = request.data.get("service_name")

        # Validate in       
        if not username or not service_name:
            return Response({"error": "Username and service_name are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Get the user
        user = get_object_or_404(CustomUser, username=username)

        # Get the patient's assigned care manager
        patient = get_object_or_404(Patient, user=user)
        care_manager = patient.care_manager

        if not care_manager:
            return Response({"error": "No care manager assigned to this user."}, status=status.HTTP_400_BAD_REQUEST)

        # Create a ticket
        ticket_data = {
            "user_initiated": user,
            "user_assigned": care_manager,
            "service_name": service_name,
            "status":"OPEN",
            "current_work": "Assigned to care manager, will get back ASAP",
        }

        result = create_or_update_ticket(**ticket_data)
        send_email(f"{username} intiated service request for {service_name}",f"{username} intiated service request for {service_name}",[care_manager.email])
        return Response(result, status=status.HTTP_201_CREATED)
    
def send_email(subject, message, recipient_emails):
    send_mail(
        subject,
        message,
        "sairamp@caresanctum.com",  # Must be a verified sender email
        recipient_emails,
        fail_silently=False,
    )


@api_view(["GET"])
def get_tickets(request):
    """
    API to fetch tickets based on filters like username, status, and assigned care manager.
    """
    username = request.query_params.get("username", None)
    status = request.query_params.get("status", None)
    assigned_care_manager = request.query_params.get("assigned_care_manager", None)

    tickets = Ticket.objects.all()

    if username:
        tickets = tickets.filter(user_initiated__username=username)

    if status:
        tickets = tickets.filter(status=status)

    if assigned_care_manager:
        tickets = tickets.filter(user_assigned__username=assigned_care_manager)

    serializer = TicketSerializer(tickets, many=True)
    return Response(serializer.data, status=200)


class ScheduleVisitAPIView(APIView):
    """
    API to create or update a scheduled visit
    """
    def post(self, request):
        username = request.data.get("username")
        visit_type = request.data.get("visit_type")
        acess_token = get_zoom_access_token()
        scheduled_datetime = request.data.get("scheduled_datetime", None)
        gmeet_link = create_zoom_meeting(acess_token)
        status_val = request.data.get("status", "scheduled")

        patient = get_object_or_404(Patient, user__username=username)

        # Check if rescheduling an existing visit
        existing_visit = ScheduledVisit.objects.filter(patient=patient, visit_type=visit_type).first()
        
        if existing_visit:
            existing_visit.scheduled_datetime = scheduled_datetime
            existing_visit.gmeet_link = gmeet_link
            existing_visit.status = status_val
            existing_visit.save()
            return Response({"message": "Visit rescheduled successfully","meet_link":gmeet_link}, status=status.HTTP_200_OK)
        
        # Create new visit
        visit = ScheduledVisit.objects.create(
            patient=patient,
            visit_type=visit_type,
            scheduled_datetime=scheduled_datetime,
            gmeet_link=gmeet_link,
            status=status_val
        )
        
        return Response({"message": "Visit scheduled successfully","meet_link":gmeet_link})


class GetPatientSchedulesAPIView(APIView):
    """
    API to retrieve all scheduled visits for a patient
    """
    def get(self, request, username):
        patient = get_object_or_404(Patient, user__username=username)
        visits = ScheduledVisit.objects.filter(patient=patient)
        serializer = ScheduledVisitSerializer(visits, many=True)
        return Response(serializer.data)


CLIENT_ID = "8it80gwjQRO8xHh5wwznyg"
CLIENT_SECRET = "u24seLpQjjSO2Ztx51bayltbCnY0u93R"
ACCOUNT_ID = "YdqyF8EdT3WmfgW7sk35qQ"

def get_zoom_access_token():
    url = "https://zoom.us/oauth/token"
    headers = {"Authorization": f"Basic {CLIENT_ID}:{CLIENT_SECRET}"}
    payload = {
        "grant_type": "account_credentials",
        "account_id": ACCOUNT_ID
    }

    response = requests.post(url, headers=headers, data=payload)
    token_data = response.json()
    return token_data.get("access_token")




def create_zoom_meeting(ZOOM_API_KEY):
    url = "https://api.zoom.us/v2/users/me/meetings"
    headers = {
        "Authorization": f"Bearer {ZOOM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "topic": "Scheduled Visit",
        "type": 2,
        "start_time": "2025-02-22T10:00:00Z",
        "duration": 30,
        "timezone": "Asia/Kolkata",
        "settings": {"host_video": True, "participant_video": True},
    }

    response = requests.post(url, headers=headers, json=payload)
    meeting_data = response.json()
    print(meeting_data)
    return meeting_data.get("join_url")


@api_view(["GET"])
def     latest_community_events(request):
    """Fetch latest 3 upcoming community events."""
    events = CommunityEvent.objects.filter(date__gte=now()).order_by("date")[:3]
    serializer = CommunityEventSerializer(events, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["POST"])
def register_for_event(request):
    """Allow a user to register for a community event."""
    username = request.data.get("username")
    event_name = request.data.get("event_name")

    if not username or not event_name:
        return Response({"error": "Username and Event Name are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(username=username)
        event = CommunityEvent.objects.get(name=event_name)

        # Add user to event
        event.registered_users.add(user)
        event.total_registered = event.registered_users.count()
        event.save()

        return Response({"message": f"{username} successfully registered for {event_name}"}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except CommunityEvent.DoesNotExist:
        return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)




@api_view(["GET"])
def get_all_medications(request):
    """Fetch all medications for all users."""
    medications = CurrentMedication.objects.all()
    serializer = CurrentMedicationSerializer(medications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
def get_user_medications(request, username):
    """Fetch medications for a specific user with status filtering (default: current)."""
    status_filter = request.GET.get("status", "current")  # Default is 'current'

    try:
        user = User.objects.get(username=username)
        medications = CurrentMedication.objects.filter(user=user, status=status_filter)
        serializer = CurrentMedicationSerializer(medications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
