import os
from core.settings.base import *
from dotenv import load_dotenv
from core.logging import *

# Load environment variables from .env file
load_dotenv(Path.joinpath(BASE_DIR, '.env/env_devel'))

SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DB_NAME', default=''),
        'USER': os.getenv('DB_USER', default=''),
        'PASSWORD': os.getenv('DB_PASSWORD', default=''),
        'HOST': os.getenv('DB_HOST', default=''),
        'PORT': os.getenv('DB_PORT', default=''),
        'CONN_MAX_AGE': 600,  # connection persistence for 10 minutes
    }
}

STATIC_ROOT = Path.joinpath(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    Path.joinpath(BASE_DIR, 'static'),
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Email settings
# EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', default='')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER', default='')