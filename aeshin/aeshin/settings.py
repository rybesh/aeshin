import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

from secrets import *

# database ---------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3')
    }
}

# debugging --------------------------------------------------------------------

DEBUG = True
TEMPLATE_DEBUG = True

# email ------------------------------------------------------------------------

ADMINS = (
    ('Ryan Shaw', 'ryanshaw@unc.edu'),
)
MANAGERS = ADMINS
DEFAULT_FROM_EMAIL = 'Ryan Shaw <ryanshaw@unc.edu>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'ryan.b.shaw@gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# file uploads -----------------------------------------------------------------

# MEDIA_ROOT = ''
MEDIA_URL = '/files/'

# globalization ----------------------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'US/Eastern'
USE_I18N = False
USE_L10N = False
USE_TZ = True

# http -------------------------------------------------------------------------

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'aeshin.middleware.ShortURLMiddleware',
    'aeshin.middleware.XUACompatibleMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

WSGI_APPLICATION = 'aeshin.wsgi.application'

# models -----------------------------------------------------------------------

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'south',
    'shared',
    'courses',
    'files',
    'brevisurl',
)

# security ---------------------------------------------------------------------

ALLOWED_HOSTS = []

# templates --------------------------------------------------------------------

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_DIRS = (
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates')),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
)

# urls -------------------------------------------------------------------------

ROOT_URLCONF = 'aeshin.urls'

# django.contrib.auth ----------------------------------------------------------

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/loggedin/'
LOGOUT_URL = '/logout/'

# django.contrib.sites ---------------------------------------------------------

SITE_ID = 1

# django.contrib.staticfiles ---------------------------------------------------

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'static')),
)

# shared -----------------------------------------------------------------------

ZOTERO_GROUP_ID = '51755'

