"""Django settings for the AI PM SaaS."""

import os
from pathlib import Path
from datetime import timedelta

from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-secret")

DEBUG = config("DEBUG", default=0, cast=int) == 1

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="*",
    cast=Csv()
)

INSTALLED_APPS = [
    "daphne",

    # Django Apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    # Third Party Apps
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",

    "corsheaders",
    "channels",
    "channels_redis",
    "django_filters",
    "drf_spectacular",

    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    "dj_rest_auth",
    "dj_rest_auth.registration",

    # Local Apps
    "apps.accounts",
    "apps.projects",
    "apps.tasks",
    "apps.notifications",
    "apps.analytics",
    "apps.ai_engine",
    "apps.realtime",
    "apps.uploads",
]

SITE_ID = 1

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.security.SecurityMiddleware",

    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "allauth.account.middleware.AccountMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    "apps.accounts.middleware.AuditLogMiddleware",
]

ROOT_URLCONF = "core.urls"

WSGI_APPLICATION = "core.wsgi.application"

ASGI_APPLICATION = "core.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates"
        ],

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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",

        "NAME": config(
            "MYSQLDATABASE",
            default="railway"
        ),

        "USER": config(
            "MYSQLUSER",
            default="root"
        ),

        "PASSWORD": config(
            "MYSQLPASSWORD",
            default=""
        ),

        "HOST": config(
            "MYSQLHOST",
            default="localhost"
        ),

        "PORT": config(
            "MYSQLPORT",
            default="3306"
        ),

        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = config(
    "REDIS_URL",
    default="redis://localhost:6379/0"
)

CELERY_BROKER_URL = REDIS_URL

CELERY_RESULT_BACKEND = REDIS_URL

CELERY_ACCEPT_CONTENT = ["json"]

CELERY_TASK_SERIALIZER = "json"

CELERY_RESULT_SERIALIZER = "json"

CELERY_TIMEZONE = TIME_ZONE

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",

        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",

        "LOCATION": REDIS_URL,
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),

    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),

    "DEFAULT_PAGINATION_CLASS":
        "rest_framework.pagination.PageNumberPagination",

    "PAGE_SIZE": 25,

    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),

    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),

    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "1000/min",
    },

    "DEFAULT_SCHEMA_CLASS":
        "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":
        timedelta(
            minutes=config(
                "JWT_ACCESS_LIFETIME_MIN",
                default=60,
                cast=int
            )
        ),

    "REFRESH_TOKEN_LIFETIME":
        timedelta(
            days=config(
                "JWT_REFRESH_LIFETIME_DAYS",
                default=14,
                cast=int
            )
        ),

    "ROTATE_REFRESH_TOKENS": True,

    "BLACKLIST_AFTER_ROTATION": True,

    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="https://synapseai-9h70.onrender.com",
    cast=Csv()
)

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "https://synapseai-9h70.onrender.com"
]

REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_HTTPONLY": False,
    "SESSION_LOGIN": False,
}

SECURE_BROWSER_XSS_FILTER = True

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"

SESSION_COOKIE_HTTPONLY = True

CSRF_COOKIE_HTTPONLY = False

SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_SECURE = not DEBUG

OPENAI_API_KEY = config(
    "OPENAI_API_KEY",
    default=""
)

GEMINI_API_KEY = config(
    "GEMINI_API_KEY",
    default=""
)

ACCOUNT_EMAIL_VERIFICATION = "none"

ACCOUNT_AUTHENTICATION_METHOD = "email"

ACCOUNT_EMAIL_REQUIRED = True

ACCOUNT_USERNAME_REQUIRED = False

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": config(
                "GOOGLE_OAUTH_CLIENT_ID",
                default=""
            ),

            "secret": config(
                "GOOGLE_OAUTH_CLIENT_SECRET",
                default=""
            ),

            "key": "",
        },

        "SCOPE": [
            "profile",
            "email"
        ],

        "AUTH_PARAMS": {
            "access_type": "online"
        },
    }
}

LOGGING = {
    "version": 1,

    "disable_existing_loggers": False,

    "formatters": {
        "std": {
            "format":
                "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        }
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "std",
        }
    },

    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
