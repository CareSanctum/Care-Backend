import requests
import json
from datetime import datetime, timedelta, timezone
from django.shortcuts import redirect
from django.http import JsonResponse
from django.conf import settings
from django.utils.dateparse import parse_datetime
from user_onboarding.models import GoogleFitToken
import urllib.parse
from user_onboarding.models import CustomUser

# Load client secrets
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
REDIRECT_URI = "http://127.0.0.1:8080/google-fit/callback/"

# Required Google Fit Scopes
GOOGLE_FIT_SCOPES = (
    "https://www.googleapis.com/auth/fitness.activity.read "
    "https://www.googleapis.com/auth/fitness.heart_rate.read "
    "https://www.googleapis.com/auth/fitness.blood_pressure.read "
    "https://www.googleapis.com/auth/fitness.body.read "
    "https://www.googleapis.com/auth/fitness.sleep.read "
    "https://www.googleapis.com/auth/fitness.body_temperature.read "
    "https://www.googleapis.com/auth/fitness.blood_glucose.read "
    "https://www.googleapis.com/auth/fitness.oxygen_saturation.read "
)




# Step 1: Initiate Google Fit Auth
def google_fit_auth(request):
    user_email = request.GET.get("user_email")
    if not user_email:
        return JsonResponse({"error": "Email parameter missing"})
    
    # URL-encode the user_email and include it in the state parameter
    state = urllib.parse.quote(user_email)
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        "response_type=code&"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={GOOGLE_FIT_SCOPES}&"
        "access_type=offline&"
        "prompt=consent&"
        f"state={state}"
    )
    return redirect(auth_url)


# Step 2: Handle Callback and Save Tokens
def google_fit_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state")
    if not code:
        return JsonResponse({"error": "Missing code parameter in response"})

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    user_email = urllib.parse.unquote(state)
    response = requests.post(token_url, data=data)

    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))

        if not refresh_token:
            creds = GoogleFitToken.objects.filter(user=request.user).first()
            if creds:
                refresh_token = creds.refresh_token

        if tokens:
            GoogleFitToken.objects.update_or_create(
                user=CustomUser.objects.get(email=user_email),
                defaults={
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": expires_at,
                },
            )
            return JsonResponse({"message": "Google Fit Auth Successful!", "tokens": tokens})
        else:
            request.session["google_fit_credentials"] = {
                "token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at.isoformat(),
            }
            return JsonResponse({"message": "Google Fit Auth Successful!", "tokens": tokens})
    else:
        return JsonResponse({"error": "Failed to retrieve tokens", "details": response.json()})

from datetime import datetime, timedelta
import requests
from django.http import JsonResponse

# Step 3: Fetch Google Fit Data
def fetch_google_fit_data(request):
    # creds = get_google_fit_creds(request)
    # if not creds:
    #     return JsonResponse({"error": "No credentials found. Please authorize again."})

    access_token = request.GET.get("access_token")

    google_fit_url = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"

    # ✅ Fix to include today's data until midnight
    now_utc=datetime.now(timezone.utc)
    end_time = now_utc.replace(hour=23, minute=59, second=59, microsecond=999999)
    start_time = end_time - timedelta(days=7)  # 7 days including today
    duration=86400000


    start_time_millis = int(start_time.timestamp() * 1000)
    end_time_millis = int(end_time.timestamp() * 1000)

    request_body = {
        "aggregateBy": [
            {"dataTypeName": "com.google.step_count.delta"},  # Steps
            {"dataTypeName": "com.google.heart_rate.bpm"},   # Heart Rate
            {"dataTypeName": "com.google.blood_pressure"},   # Blood Pressure
            {"dataTypeName": "com.google.weight"},           # Weight
            {"dataTypeName": "com.google.sleep.segment"},    # Sleep
            {"dataTypeName": "com.google.body.temperature"},
            {"dataTypeName": "com.google.blood_glucose"},
        ],
        "bucketByTime": {"durationMillis": 86400000},  # 1 day
        "startTimeMillis": start_time_millis,
        "endTimeMillis": end_time_millis,
    }

    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    response = requests.post(google_fit_url, json=request_body, headers=headers)

    if response.status_code != 200:
        return JsonResponse({"error": "Failed to fetch Google Fit data."})

    google_fit_data = response.json()
    processed_data = process_google_fit_data(google_fit_data, start_time)

    return JsonResponse(processed_data, safe=False)


# Step 4: Process Google Fit Data
def process_google_fit_data(data, start_time):
    result = {}

    for i, bucket in enumerate(data.get("bucket", [])):
        start_time_millis = int(bucket["startTimeMillis"])
        start_date = datetime.utcfromtimestamp(start_time_millis / 1000).strftime('%Y-%m-%d')

        # ⚡️ To use "day 1", "day 2", ..., uncomment this line
        day_label = f"day {i + 1}"  
        
        # ⚡️ To use specific dates like "2025-03-16", uncomment this line
        day_label = start_date  

        result[day_label] = {
            "step_count": 0,
            "heart_rate": 0,
            "systolic": 0,
            "diastolic": 0,
            "weight": 0,
            "sleep_duration": 0,
            "body_temperature": 0.0,
            "blood_glucose": 0.0,
        }

        for dataset in bucket.get("dataset", []):
            for point in dataset.get("point", []):
                value = point.get("value", [])[0]

                if "com.google.step_count.delta" in dataset["dataSourceId"]:
                    result[day_label]["step_count"] += value.get("intVal", 0)

                elif "com.google.blood_glucose" in dataset["dataSourceId"]:
                    result[day_label]["blood_glucose"] = value.get("fpVal", 0.0)
                
                elif "com.google.body.temperature" in dataset["dataSourceId"]:
                    result[day_label]["body_temperature"] = value.get("fpVal", 0.0)

                elif "com.google.heart_rate.bpm" in dataset["dataSourceId"]:
                    result[day_label]["heart_rate"] = value.get("fpVal", 0.0)

                elif "com.google.blood_pressure" in dataset["dataSourceId"]:
                    systolic = value.get("mapVal", [])[0].get("fpVal", 0.0) if value.get("mapVal") else 0.0
                    diastolic = value.get("mapVal", [])[1].get("fpVal", 0.0) if len(value.get("mapVal", [])) > 1 else 0.0
                    result[day_label]["systolic"] = systolic
                    result[day_label]["diastolic"] = diastolic

                elif "com.google.weight" in dataset["dataSourceId"]:
                    result[day_label]["weight"] = value.get("fpVal", 0.0)

                elif "com.google.sleep.segment" in dataset["dataSourceId"]:
                    result[day_label]["sleep_duration"] += value.get("intVal", 0)

    return result



# Step 4: Refresh Google Fit Token (if expired)
def refresh_google_fit_token(request):
    creds = get_google_fit_creds(request)
    if not creds:
        return JsonResponse({"error": "No credentials found. Please authorize again."})

    refresh_token = creds.refresh_token if request.user.is_authenticated else creds["refresh_token"]

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        new_tokens = response.json()
        access_token = new_tokens["access_token"]
        expires_at = datetime.utcnow() + timedelta(seconds=new_tokens["expires_in"])

        if request.user.is_authenticated:
            creds.access_token = access_token
            creds.expires_at = expires_at
            creds.save()
        else:
            request.session["google_fit_credentials"]["token"] = access_token
            request.session["google_fit_credentials"]["expires_at"] = expires_at.isoformat()

        return JsonResponse({"message": "Token refreshed successfully!", "access_token": access_token})
    else:
        return JsonResponse({"error": "Failed to refresh token. Please re-authenticate.", "details": response.json()})


# Utility Function: Get Google Fit Credentials
def get_google_fit_creds(request):
    """Retrieve Google Fit credentials for authenticated or session-based users."""
    if request.user.is_authenticated:
        return GoogleFitToken.objects.filter(user=request.user).first()
    else:
        return request.session.get("google_fit_credentials")