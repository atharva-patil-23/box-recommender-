"""Django settings, configured from the environment (12-factor).

All deployment-specific values come from environment variables (optionally loaded
from a local ``.env`` file). There is no SQLite fallback: the same PostgreSQL
engine is used locally, in Docker, and in CI so behaviour never drifts.
"""

from pathlib import Path

import django_stubs_ext
import environ
from django.core.exceptions import ImproperlyConfigured

# Make generic subscripts like ModelAdmin[Product] work at runtime (django-stubs).
django_stubs_ext.monkeypatch()

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
# Load a local .env if present; real environments inject vars directly.
environ.Env.read_env(BASE_DIR / ".env")

_INSECURE_SECRET_KEY = "dev-insecure-secret-key-change-me"
DEBUG = env.bool("DEBUG")
SECRET_KEY = env("SECRET_KEY", default=_INSECURE_SECRET_KEY)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# Never run with the throwaway development key outside DEBUG.
if not DEBUG and SECRET_KEY == _INSECURE_SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY must be set to a real value when DEBUG is False.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "inventory",
    "orders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Single source of truth for the database: DATABASE_URL. The default points at the
# Docker Compose Postgres so local development works out of the box, still on Postgres.
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://app:app@localhost:5432/app",
    ),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}
