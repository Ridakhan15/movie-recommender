import os
from pathlib import Path

# ----------------------------------------------
# BASE DIRECTORY
# ----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

USE_POSTGRES = os.environ.get('USE_POSTGRES', 'False') == 'True'


# ----------------------------------------------
# SECURITY SETTINGS
# ----------------------------------------------
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # ADD THIS
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    ...
]

# ----------------------------------------------
# APPLICATIONS
# ----------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'recommender',
    'abtesting',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'recommendation_project.urls'


# ----------------------------------------------
# TEMPLATES
# ----------------------------------------------
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

WSGI_APPLICATION = 'recommendation_project.wsgi.application'


# ----------------------------------------------
# DATABASE CONFIGURATION
# ----------------------------------------------
# Automatically switch between SQLite (local) and PostgreSQL (production)
if USE_POSTGRES:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'movie_recommender'),
            'USER': os.environ.get('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
            'HOST': os.environ.get('DB_HOST', 'db'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ----------------------------------------------
# PASSWORD VALIDATION
# ----------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ----------------------------------------------
# INTERNATIONALIZATION
# ----------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ----------------------------------------------
# STATIC FILES
# ----------------------------------------------
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",  # your development static folder
]

STATIC_ROOT = BASE_DIR / "staticfiles"  # for collectstatic in production




# ----------------------------------------------
# DEFAULT PRIMARY KEY FIELD TYPE
# ----------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ----------------------------------------------
# LOGIN / LOGOUT SETTINGS
# ----------------------------------------------
# Redirect URL when login is required
LOGIN_URL = '/login/'        # This tells Django where the login page actually is
LOGIN_REDIRECT_URL = '/'     # After login, where to redirect
LOGOUT_REDIRECT_URL = '/login/'  # After logout, redirect to login



# ----------------------------------------------
# DJANGO REST FRAMEWORK SETTINGS
# ----------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# ADD THESE LINES TO THE BOTTOM OF YOUR EXISTING SETTINGS.PY

# ==================================
# CELERY CONFIGURATION (Real-Time Updates)
# ==================================

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery Beat Schedule (for periodic tasks)
CELERY_BEAT_SCHEDULE = {
    'retrain-models-daily': {
        'task': 'recommender.tasks.retrain_all_models',
        'schedule': 86400.0,  # 24 hours
    },
    'process-pending-updates': {
        'task': 'recommender.tasks.process_model_updates',
        'schedule': 300.0,  # 5 minutes
    },
}


STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
