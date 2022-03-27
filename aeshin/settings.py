import os

from .secrets import * # noqa

WWW_ROOT = '.'

# database --------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(WWW_ROOT, 'db.sqlite3')
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# debugging -------------------------------------------------------------------

DEBUG = False
TEMPLATE_DEBUG = False

# logging ---------------------------------------------------------------------

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': False,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
        },
    },
}

# email -----------------------------------------------------------------------

ADMINS = (
    ('Ryan Shaw', 'rieyin@icloud.com'),
)
MANAGERS = ADMINS
DEFAULT_FROM_EMAIL = 'aeshin.org <no-reply@aeshin.org>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_HOST_USER = 'postmaster@kimyuenikk.aeshin.org'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# file uploads ----------------------------------------------------------------

MEDIA_DIR = 'media/'
MEDIA_ROOT = os.path.join(WWW_ROOT, MEDIA_DIR)
MEDIA_URL = '/files/'

# globalization ---------------------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'US/Eastern'
USE_I18N = False
USE_TZ = True

# http ------------------------------------------------------------------------

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

WSGI_APPLICATION = 'aeshin.wsgi.application'

# models ----------------------------------------------------------------------

INSTALLED_APPS = (
    'aeshin',
    'shared',
    'courses',
    'files',
    'shuffle',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
)

# security --------------------------------------------------------------------

ALLOWED_HOSTS = [
    '.aeshin.org',
    '.aeshin.org.',
    '127.0.0.1',
]

# templates -------------------------------------------------------------------

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.contrib.auth.context_processors.auth',
            'django.template.context_processors.debug',
            'django.template.context_processors.media',
            'django.template.context_processors.static',
            'django.template.context_processors.tz',
            'django.contrib.messages.context_processors.messages',
            'django.template.context_processors.request',
        ]
    }
}]

# urls ------------------------------------------------------------------------

ROOT_URLCONF = 'aeshin.urls'

# django.contrib.auth ---------------------------------------------------------

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/loggedin/'
LOGOUT_URL = '/logout/'

# django.contrib.sites --------------------------------------------------------

SITE_ID = 1

# django.contrib.staticfiles --------------------------------------------------

STATIC_ROOT = os.path.join(WWW_ROOT, 'static')
STATIC_URL = '/static/'

# shared ----------------------------------------------------------------------

ZOTERO_GROUP_ID = '51755'
