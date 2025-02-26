from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
# import requests
import uuid
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
import datetime
from rest_framework import serializers, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

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
    "LabReport": {
        "LR_file": "LR_file_url",
    },
    "Prescription": {
        "Presc_file": "Presc_file_url",
    }
}


class FileUploadAPIView(APIView):
    parser_classes = [MultiPartParser]
    def post(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        field_name = request.data.get("name")  # Optional
        user_name = request.data.get("user_name")  # Optional
        test_name = request.data.get("test_name")  # Optional
        doctor_name = request.data.get("doctor_name")  # Optional
        prescribed_date = request.data.get("prescribed_date")  # Optional
        test_date = request.data.get("test_date")  # Optional

        if not file:
            return Response({"error": "File is required"}, status=status.HTTP_400_BAD_REQUEST)
        

        # Determine target model
        model = None
        instance = None
        folder = "uploads"  # Default folder if no specific user is given
        model_name = None

        # Determine target model
        if field_name in ALLOWED_FIELDS["Patient"] and user_name:
            model = Patient
            instance = Patient.objects.filter(user__username=user_name).first()
            folder = f"patients/{user_name}"
            model_name = "Patient"
        elif field_name in ALLOWED_FIELDS["MedicalHistory"] and user_name:
            model = MedicalHistory
            instance = MedicalHistory.objects.filter(patient__user__username=user_name).first()
            folder = f"medical_history/{user_name}"
            model_name = "MedicalHistory"
        elif field_name in ALLOWED_FIELDS["LabReport"]:
            if not user_name:
                return Response({"error": "User name is required for LabReport"}, status=status.HTTP_400_BAD_REQUEST)

            user = CustomUser.objects.filter(username=user_name).first()
            if not user:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            instance, _ = LabReport.objects.get_or_create(
                user=user,
                test_name=test_name if test_name else "",
                test_date=test_date if test_date else None
            )
            folder = f"lab_reports/{user_name}"
            model_name = "LabReport"
        elif field_name in ALLOWED_FIELDS["Prescription"]:
            user_instance = CustomUser.objects.filter(username=user_name).first() if user_name else None
            if not user_instance:
                return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

            instance, _ = Prescription.objects.get_or_create(
                user=user_instance,
                doctor_name=doctor_name if doctor_name else "",
                prescribed_date=prescribed_date if prescribed_date else None
            )
            folder = f"prescriptions/{user_name if user_name else 'general'}"
            model_name = "Prescription"
        else:
            return Response({"error": "Invalid field name or missing user_name"}, status=status.HTTP_400_BAD_REQUEST)

        # Define correct field
        field_to_update = ALLOWED_FIELDS[model_name].get(field_name)
        if not field_to_update:
            return Response({"error": "Invalid field mapping"}, status=status.HTTP_400_BAD_REQUEST)

        # Define file path in S3
        s3_path = f"{folder}/{field_name}/{file.name}"

        try:
            # Upload file to S3
            s3.upload_fileobj(file, BUCKET_NAME, s3_path, ExtraArgs={"ACL": "public-read"})

            # Generate public file URL
            file_url = f"https://{BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_path}"

            # Update the model field with the S3 URL if instance exists
            if instance:
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
        email_body = f"""
Dear Care Manager,

I hope this message finds you well.

We would like to inform you that {username} initiated a service request for {service_name}.

User Details:
- Username: {username}
- Contact: {user.phone_number}
- Email: {user.email}

Please review and take necessary action on this request.

If you need any further information, feel free to reach out.

Best regards,
CareSanctum
"""
        send_email(f"Service Request Notification for {username}",email_body,[care_manager.email])
        return Response(result, status=status.HTTP_201_CREATED)
    
def send_email(subject, message, recipient_emails):
    try:
        send_mail(
            subject,
            message,
            "sairamp@caresanctum.com",  # Must be a verified sender email
            recipient_emails,
            fail_silently=False,
        )
        print(f"Email sent to {recipient_emails}")
    except Exception as e:
        print(f"Error sending email: {str(e)}") 

@api_view(["POST"])
def contact_CM(request):
    username = request.data.get("username")

    if not username:
        return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    user = get_object_or_404(CustomUser, username=username)

    # Get the patient's assigned care manager
    patient = get_object_or_404(Patient, user=user)
    care_manager = patient.care_manager

    if not care_manager:
        return Response({"error": "No care manager assigned to the user"}, status=status.HTTP_400_BAD_REQUEST)
    
    email_body = f"""
Dear Care Manager,

I hope this message finds you well.

We would like to inform you that {username} has initiated a contact request:

User Details:
- Username: {username}
- Contact: {user.phone_number}
- Email: {user.email}


Please review the message and get in touch with the user as soon as possible.

If you need any further information, feel free to reach out.

Best regards,
CareSanctum
"""
    
    send_email(f"User {username} has contacted you",email_body,[care_manager.email])
    print ("request received")
    return Response({"message": "Mail Sent to Care Manager. They will reach out to you shortly"}, status=status.HTTP_200_OK)


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
        scheduled_datetime = request.data.get("scheduled_datetime", None)
        gmeet_link = generate_meeting_link()
        status_val = request.data.get("status", "scheduled")

        patient = get_object_or_404(Patient, user__username=username)

        # Check if rescheduling an existing visit
        existing_visit = ScheduledVisit.objects.filter(patient=patient, visit_type=visit_type).first()
        
        if existing_visit:
            existing_visit.scheduled_datetime = scheduled_datetime
            existing_visit.gmeet_link = gmeet_link
            existing_visit.status = "rescheduled"
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


JITSI_SERVER_URL = "https://meet.jit.si"

def generate_meeting_link():
    """Generates a unique Jitsi Meet link."""
    meeting_id = str(uuid.uuid4())  # Generate a unique identifier
    meeting_link = f"{JITSI_SERVER_URL}/{meeting_id}"
    return meeting_link



@api_view(["GET"])
def latest_community_events(request):
    """Fetch latest 3 upcoming community events."""
    events = CommunityEvent.objects.all()
    serializer = CommunityEventSerializer(events, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["POST"])
def register_for_event(request):
    """Allow a user to register for a community event."""
    username = request.data.get("username")
    event_id = request.data.get("event_id")

    if not username or not event_id:
        return Response({"error": "Username and Event Name are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(username=username)
        event = CommunityEvent.objects.get(id=event_id)

        # Add user to event
        event.registered_users.add(user)
        event.total_registered = event.registered_users.count()
        event.save()

        return Response({"message": f"{username} successfully registered for {event_id}"}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except CommunityEvent.DoesNotExist:
        return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)


# ViewSets
class MedicationViewSet(viewsets.ModelViewSet):
    @action(detail=False, methods=['post'])
    def upload_document(self, request):
        username = request.data.get("username")
        file = request.FILES.get("file")
        medicine_name = request.data.get("medicine_name")
        dosage = request.data.get("dosage")
        timing = request.data.get("timing")
        prescribed_by = request.data.get("prescribed_by")
        expiry_date = request.data.get("exp_date")
        
        if not username or not file:
            return Response({"error": "Username and file are required"}, status=400)
        
        user = CustomUser.objects.filter(username=username).first()
        if not user:
            return Response({"error": "User not found"}, status=400)
        
        # Upload file to S3
        bucket_name = BUCKET_NAME
        file_key = f"medical_documents/{username}/{file.name}"
        s3.upload_fileobj(file, bucket_name, file_key, ExtraArgs={'ACL': 'public-read'})
        file_url = f"https://{bucket_name}.s3.amazonaws.com/{file_key}"

        # Create an empty medication record
        medication = CurrentMedication.objects.create(
            user=user,medicine_name=medicine_name,dosage=dosage,timing=timing,prescribed_by=prescribed_by,stock_remaining=0,expiry_date=expiry_date)
        
        # Store document URL in MedicalDocument
        MedicalDocuments.objects.create(medication=medication, document_url=file_url)
        return Response({"message": "File uploaded successfully", "document_url": file_url}, status=201)


    @action(detail=False, methods=['get'])
    def get_medications(self, request):
        username = request.query_params.get("username")
        if not username:
            return Response({"error": "Username is required"}, status=400)
        
        user = CustomUser.objects.filter(username=username).first()
        if not user:
            return Response({"error": "User not found"}, status=400)
        
        medications = CurrentMedication.objects.filter(user=user)
        serializer = MedicationSerializer(medications, many=True)
        return Response(serializer.data, status=200)

@api_view(["GET"])
def get_patient_details(request, username):
    try:
        patient = Patient.objects.select_related("care_manager", "admin", "kin").get(user__username=username)
        serializer = PatientDetailSerializer(patient)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Patient.DoesNotExist:
        return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
    

@api_view(["GET"])
def get_prescriptions(request, username):
    user = get_object_or_404(CustomUser, username=username)

    # Get lab reports for the user
    Prescription_list = Prescription.objects.filter(user=user)

    # if not Prescription_list.exists():
    #     return Response({"message": "No Prescriptions found for this user."}, status=status.HTTP_404_NOT_FOUND)

    serializer = PrescriptionSerializer(Prescription_list, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["POST"])
def add_prescription(request):
    serializer = PrescriptionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Lab Reports - GET and POST APIs
@api_view(["GET"])
def get_lab_reports(request, username):
    user = get_object_or_404(CustomUser, username=username)

    # Get lab reports for the user
    lab_reports = LabReport.objects.filter(user=user)

    # if not lab_reports.exists():
    #     return Response({"message": "No lab reports found for this user."}, status=status.HTTP_404_NOT_FOUND)

    serializer = LabReportSerializer(lab_reports, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["POST"])
def add_lab_report(request):
    serializer = LabReportSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignedPatientsView(APIView):
    def get(self, request, care_manager_username):
        try:
            care_manager = CustomUser.objects.get(username=care_manager_username, role="CARE_MANAGER")
        except CustomUser.DoesNotExist:
            return Response({"error": "Care Manager not found"}, status=status.HTTP_404_NOT_FOUND)

        assigned_users = CustomUser.objects.filter(patient_profile__care_manager=care_manager)
        serializer = CustomUserSerializer(assigned_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)