import os

from .secrets import * # noqa

WWW_ROOT = '/var/www/aeshin.org'

# database --------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(WWW_ROOT, 'db.sqlite3')
    }
}

# debugging -------------------------------------------------------------------

DEBUG = False
TEMPLATE_DEBUG = False

# logging ---------------------------------------------------------------------

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}

# email -----------------------------------------------------------------------

ADMINS = (
    ('Ryan Shaw', 'ryanshaw@unc.edu'),
)
MANAGERS = ADMINS
DEFAULT_FROM_EMAIL = 'Ryan Shaw <ryanshaw@unc.edu>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_HOST = 'smtp.office365.com'
EMAIL_HOST_USER = 'ryanshaw@ad.unc.edu'
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
USE_L10N = False
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
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'aeshin',
    'shared',
    'courses',
    'files',
    'shuffle',
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
    'DIRS': [
        os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates')),
    ],
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
STATICFILES_DIRS = (
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'static')),
)

# shared ----------------------------------------------------------------------

ZOTERO_GROUP_ID = '51755'
