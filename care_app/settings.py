"""
Django settings for care_app project.
Generated by 'django-admin startproject' using Django 4.2.3.
For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

# To load Environment Varibles 
import os 
from dotenv import load_dotenv
from pathlib import Path
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure--yghem+^5tk@p_vor(vw_jbm_xcecyer*1@(f&iu65poj5(#n7'
# SECURITY WARNING: don't run with debug turned on in production!


DEBUG = os.getenv("DEBUG", "False") == "True"
# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "user_onboarding",
    "corsheaders",
    "whitenoise.runserver_nostatic"
]
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Add this line at the top
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

                           
ROOT_URLCONF = 'care_app.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "apikey"  # This is the fixed value for SendGrid
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")  # Replace with your API Key
DEFAULT_FROM_EMAIL = "sairamp@caresanctum.com"


WSGI_APPLICATION = 'care_app.wsgi.application'

if DEBUG:
    ALLOWED_HOSTS = ["*"]
    CORS_ALLOW_ALL_ORIGINS = True  # Set to True to allow all, not recommended for production
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:8081",  # Your React frontend
        "http://localhost:8080",
        "http://localhost:8082",
        "https://jocular-moonbeam-bc725b.netlify.app",
        "https://webapp.caresanctum.com",
    ]
    CORS_ALLOW_HEADERS = ["Authorization", "Content-Type"]
    CORS_ALLOW_CREDENTIALS = True

    DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
    
else:
    ALLOWED_HOSTS = [
        "https://15.206.160.34",
        "https://webapp.caresanctum.com", 
        "https://jocular-moonbeam-bc725b.netlify.app",
        "https://backendapp.caresanctum.com"]
    CORS_ALLOW_ALL_ORIGINS = False  # Set to True to allow all, not recommended for production
    CORS_ALLOWED_ORIGINS = [
        #EC2 Public IP
        "https://15.206.160.34",
        "https://backendapp.caresanctum.com", #backend domain
        "https://webapp.caresanctum.com", #webapp domain
        "https://jocular-moonbeam-bc725b.netlify.app" #backup netlify domain
    ]
    CORS_ALLOW_HEADERS = ["Authorization", "Content-Type"]
    CORS_ALLOW_CREDENTIALS = True

    DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("DB_NAME"),
	    'USER': os.getenv("DB_USER"),
	    'PASSWORD': os.getenv("DB_PASSWORD"),
	    'HOST': os.getenv("DB_HOST"),
	    'PORT': os.getenv("DB_PORT"),
    }
}




#AWS S3 Bucket Configuration
load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_TZ = True
USE_I18N = True
USE_TZ = True
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}
from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}
AUTH_USER_MODEL = "user_onboarding.CustomUser"