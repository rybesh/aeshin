import os
import environ
from pathlib import Path
from django.db.models.query import QuerySet
from warnings import filterwarnings

# environment variables -------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / ".env")
env = environ.Env(DEBUG=(bool, False))

# typing ----------------------------------------------------------------------

QuerySet.__class_getitem__ = classmethod(
    lambda cls, *args, **kwargs: cls  # pyright: ignore
)

# database --------------------------------------------------------------------

DATABASES = {"default": env.db()}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# debugging -------------------------------------------------------------------

DEBUG = env("DEBUG")
TEMPLATE_DEBUG = False

# logging ---------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": False,
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
        },
    },
}

# email -----------------------------------------------------------------------

ADMINS = (("Ryan Shaw", "rieyin@icloud.com"),)
MANAGERS = ADMINS
DEFAULT_FROM_EMAIL = "aeshin.org <no-reply@aeshin.org>"
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_HOST = "email-smtp.us-east-1.amazonaws.com"
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# file uploads ----------------------------------------------------------------

MEDIA_ROOT = env.path("MEDIA_ROOT", default=BASE_DIR / "media/")
MEDIA_URL = "files/"

# globalization ---------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "US/Eastern"
USE_I18N = False
USE_TZ = True

# http ------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "aeshin.middleware.WWWRedirectMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

WSGI_APPLICATION = "aeshin.wsgi.application"

# models ----------------------------------------------------------------------

INSTALLED_APPS = (
    "aeshin",
    "shared",
    "courses",
    "files",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.sites",
)

# security --------------------------------------------------------------------

SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = [
    ".aeshin.org",
    ".localhost",
    "127.0.0.1",
    "[::1]",
    "aeshin.fly.dev",
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.aeshin.org",
    "https://aeshin.fly.dev",
]

# templates -------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]
        },
    }
]

# urls ------------------------------------------------------------------------

ROOT_URLCONF = "aeshin.urls"

# django.contrib.auth ---------------------------------------------------------

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/loggedin/"
LOGOUT_URL = "/logout/"

# django.contrib.sites --------------------------------------------------------

SITE_ID = 1

# django.contrib.staticfiles --------------------------------------------------

STATIC_ROOT = BASE_DIR / "static"
STATIC_URL = "/static/"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# shared ----------------------------------------------------------------------

ZOTERO_GROUP_ID = "51755"

# django nonsense

filterwarnings(
    "ignore", "The FORMS_URLFIELD_ASSUME_HTTPS transitional setting is deprecated."
)
FORMS_URLFIELD_ASSUME_HTTPS = True
