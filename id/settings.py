# coding=utf-8
import os

from settings_custom import LOCAL_APPS, LOCAL_MIDDLEWARE

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True

SITE_URL = 'http://localhost:8000'
MIAR_URL = 'http://localhost:3000'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'id',
    'oidc_provider',
    'rest_framework',
    'cacheops',
    'django_extensions',
    'behave_django',
    'raven.contrib.django.raven_compat',
    'anymail',
]

INSTALLED_APPS += LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'oidc_provider.middleware.SessionManagementMiddleware',

    # Verificación obligatorio del correo electrónico.
    # 'id.middleware.EmailValidatedMiddleware',

    # Términos y condiciones obligatorio. 
    # 'id.middleware.TermsAndConditionsMiddleware',
]

MIDDLEWARE += LOCAL_MIDDLEWARE

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
                'id.utils.context_processors.global_settings',
            ],
        },
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'brief': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
        'simple': {
            'format': '[%(levelname)s] %(asctime)s %(message)s',
            'datefmt': '%H:%M',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'filters': ['require_debug_true'],
            'formatter': 'simple',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
        },
        'oidc_provider': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

WSGI_APPLICATION = 'wsgi.application'
ROOT_URLCONF = 'id.urls'
AUTH_USER_MODEL = 'id.User'
LOGIN_REDIRECT_URL = 'accounts:profile'
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
LOGIN_URL = 'accounts:login'
REDIRECT_FIELD_NAME = "next"

EMAIL_SUBJECT_PREFIX = ''
SERVER_EMAIL = 'Mi Argentina <contacto@mailsender.com>'
DEFAULT_FROM_EMAIL = SERVER_EMAIL

# AnyMail
ANYMAIL = {
    "MAILGUN_API_KEY": "",
    "MAILGUN_SENDER_DOMAIN": "",
}
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

# Internationalization & Localization
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Statics & Media
STATIC_URL = '/static/'
STATIC_DIRS = (
    os.path.join(BASE_DIR, 'id/static'),
)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'id/media')

FIXTURES_ROOT = os.path.join(BASE_DIR, 'id/fixtures')

# Django OIDC Provider
OIDC_SESSION_MANAGEMENT_ENABLE = True
OIDC_UNAUTHENTICATED_SESSION_MANAGEMENT_KEY = ''
OIDC_IDTOKEN_PROCESSING_HOOK = 'id.oidc_provider_settings.default_idtoken_processing_hook'
OIDC_IDTOKEN_SUB_GENERATOR = 'id.oidc_provider_settings.custom_sub_generator'
OIDC_EXTRA_SCOPE_CLAIMS = 'id.oidc_provider_settings.CustomScopeClaims'
OIDC_USERINFO = 'id.oidc_provider_settings.userinfo'

DEFAULT_AUTHENTICATION_BACKENDS = 'django.contrib.auth.backends.ModelBackend'

# Django Rest Framework
REST_FRAMEWORK = {

    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
}

CACHEOPS = {
    # Cache por 48 Hs
    'id.Country': {'ops': {'fetch', 'get'}, 'timeout': 60 * 60 * 24 * 365},
    'id.Province': {'ops': {'fetch', 'get'}, 'timeout': 60 * 60 * 24 * 365},
    'id.District': {'ops': {'fetch', 'get'}, 'timeout': 60 * 60 * 24 * 365},
    'id.Locality': {'ops': {'fetch', 'get'}, 'timeout': 60 * 60 * 24 * 365},
}

try:
    from settings_custom import *
except ImportError:
    pass
