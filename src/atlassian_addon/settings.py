import os

import environ

env = environ.Env(DEBUG=(bool, False))

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = ["*"]

HOST_MIDDLEWARE_URLCONF_MAP = {
    # The atlassian connect based app
    # "atlassian.fluendo.com": "fluendo.atlassian_urls",
    # "atlassian-addon-prod.fluendo.com": "fluendo.atlassian_urls",
    # "localhost": "fluendo.atlassian_urls",
}

INTERNAL_IPS = ["127.0.0.1", "localhost"]

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE"),
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWD"),
        "HOST": env("DB_HOST"),
        "PORT": env.str("DB_PORT"),
    },
}

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "log_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "/tmp/django-DEBUG.log",
            "formatter": "simple",
        },
        # "workmodel_db": {
        #     "level": "DEBUG",
        #     "class": "workmodel.logger.LogHandler",
        #     "formatter": "simple",
        # },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_countries",
    "widget_tweaks",
    "django_atlassian.apps.DjangoAtlassianConfig",
    "django_celery_results",
    "django_celery_beat",
    "django_db_logger",
    "sales.apps.SalesConfig",
    "workmodel.apps.WorkModelConfig",
    "metabase.apps.MetabaseModelConfig",
    "fluendo.apps.FluendoConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_atlassian.middleware.JWTAuthenticationMiddleware",
]

ROOT_URLCONF = "atlassian_addon.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "atlassian_addon/templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "atlassian_addon.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), "static")
STATICFILES_DIRS = [
    (
        "atlassian_addon",
        os.path.join(os.path.dirname(BASE_DIR), "atlassian_addon", "static"),
    ),
]

# Cache
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://{}:{}/1".format(env("REDIS_HOST"), env.str("REDIS_PORT")),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# Celery related configuration
CELERY_BROKER_URL = "redis://{}:{}".format(env("REDIS_HOST"), env.str("REDIS_PORT"))
CELERY_RESULT_BACKEND = "django-db"

# Fluendo related configuration
FLUENDO = {
    "BASE_ADMIN_URL": env("FLUENDO_BASE_ADMIN_URL"),
    "FRESHSALES": {
        "ACCOUNTS_URL": "freshsales/salesaccounts/",
        "CONTACTS_URL": "freshsales/salescontacts/",
    },
    "CUSTOMERS": {
        "CUSTOMERS_URL": "customers/customer/",
        "CONTACTS_URL": "users/contact/",
        "AGREEMENTS_URL": "sales/agreement/",
    },
    "USERS": {
        "USERS_URL": "auth/user/",
    },
}
WEB_FLUENDO_API_SERVER = env("WEB_FLUENDO_API_SERVER")
WEB_FLUENDO_TOKEN = env("WEB_FLUENDO_TOKEN")

# Django Atlassian
URL_BASE = env("URL_BASE")
DJANGO_ATLASSIAN_JIRA_NAME = "Fluendo Atlassian Extensions"
DJANGO_ATLASSIAN_JIRA_DESCRIPTION = "Fluendo Atlassian Extensions"
DJANGO_ATLASSIAN_JIRA_KEY = "com.fluendo.atlassian-addon"
DJANGO_ATLASSIAN_JIRA_SCOPES = ["read", "write", "delete", "act_as_user"]
DJANGO_ATLASSIAN_CONFLUENCE_NAME = "Fluendo Atlassian Extensions"
DJANGO_ATLASSIAN_CONFLUENCE_DESCRIPTION = "Fluendo Atlassian Extensions"
DJANGO_ATLASSIAN_CONFLUENCE_KEY = "com.fluendo.atlassian-addon"
DJANGO_ATLASSIAN_CONFLUENCE_SCOPES = ["read", "write", "delete"]
DJANGO_ATLASSIAN_VENDOR_NAME = "Fluendo S.A."
DJANGO_ATLASSIAN_VENDOR_URL = "https://fluendo.com/"

# Development
if DEBUG:
    INTERNAL_IPS = ["127.0.0.1", "localhost"]
    INSTALLED_APPS += [
        "debug_toolbar",
    ]

    MIDDLEWARE += [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]
