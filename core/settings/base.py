from pathlib import Path
from django.urls import reverse_lazy


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Default url behaviors
LOGIN_REDIRECT_URL = 'dashboard:dashboard'
LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = reverse_lazy('login')

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third Party Apps
    'django_password_validators',
    'django_password_validators.password_history',
    'rest_framework',
    "crispy_forms",
    "crispy_bootstrap5",
    'django_filters',
    'auditlog',
    # 'jazzmin',
    # My Apps
    'customers',
    'contracts',
    'services',
    'signatures',
    'dashboard',
    'payments',
    'sec_reports',
    'users',
    'notifications',
]

BASE_MIDDLEWARE = [
    'django.contrib.messages.middleware.MessageMiddleware',
    'core.middleware.CustomerSelectionMiddleware',
]

DJANGO_MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

THIRD_MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
]

MIDDLEWARE = DJANGO_MIDDLEWARE + THIRD_MIDDLEWARE #+ BASE_MIDDLEWARE

ROOT_URLCONF = 'core.urls'
AUTH_USER_MODEL = 'users.CustomUser'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [Path.joinpath(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.selected_customer',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

DATABASE_ROUTERS = (
    # 'django_tenants.routers.TenantSyncRouter',
)

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        "OPTIONS": {
            "min_length": 16,
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'django_password_validators.password_history.password_validation.UniquePasswordsValidator',
        'OPTIONS': {
            'last_passwords': 5
        }
    },
    {
        'NAME': 'django_password_validators.password_character_requirements.password_validation.PasswordCharacterValidator',
        'OPTIONS': {
             'min_length_digit': 2,
             'min_length_alpha': 2,
             'min_length_special': 2,
             'min_length_lower': 2,
             'min_length_upper': 2,
             'special_characters': "~!@#$%^&*()_+{}\":;'[]"
         }
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUDITLOG_INCLUDE_ALL_MODELS=True
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"