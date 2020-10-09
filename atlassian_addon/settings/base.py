import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWD = os.environ.get('DB_PASSWD')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')

REDIS_HOST = os.environ.get('REDIS_HOST')

JIRA_SERVER = os.environ.get('JIRA_SERVER')
JIRA_USER = os.environ.get('JIRA_USER')
JIRA_TOKEN = os.environ.get('JIRA_TOKEN')

URL_BASE = os.environ.get('URL_BASE')

# Django Atlassian required configuration
DJANGO_ATLASSIAN_JIRA_NAME = "Fluendo Atlassian Extensions"
DJANGO_ATLASSIAN_JIRA_DESCRIPTION = "Fluendo Atlassian Extensions"
DJANGO_ATLASSIAN_JIRA_KEY = "com.fluendo.atlassian-addon"
DJANGO_ATLASSIAN_CONFLUENCE_NAME = "Fluendo Atlassian Extensions"
DJANGO_ATLASSIAN_CONFLUENCE_DESCRIPTION = "Fluendo Atlassian Extensions"
DJANGO_ATLASSIAN_CONFLUENCE_KEY = "com.fluendo.atlassian-addon"
DJANGO_ATLASSIAN_VENDOR_NAME = "Fluendo S.A."
DJANGO_ATLASSIAN_VENDOR_URL = "https://fluendo.com/"

# Customers Server Token Auth
WEB_FLUENDO_API_SERVER = os.environ.get('WEB_FLUENDO_API_SERVER')
WEB_FLUENDO_TOKEN = os.environ.get('WEB_FLUENDO_TOKEN')

DEBUG = os.environ.get('DJANGO_DEBUG', True)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '-eqb$&qsdzfdt1tm0=rvhht=)rye(g^_q_$+t*4x$ob16g8t#1'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

FLUENDO = {
    'BASE_ADMIN_URL': '//localhost:8000/en/admin/',
    'FRESHSALES':{
        'ACCOUNTS_URL': 'freshsales/salesaccounts/',
        'CONTACTS_URL': 'freshsales/salescontacts/',
    },
    'CUSTOMERS': {
        'CUSTOMERS_URL': 'customers/customer/',
        'CONTACTS_URL': 'users/contact/',
        'AGREEMENTS_URL': 'sales/agreement/',
    },
    'USERS':{
        'USERS_URL': 'auth/user/',
    }
}

HOST_MIDDLEWARE_URLCONF_MAP = {
    # The atlassian connect based app
    #"atlassian.fluendo.com": "fluendo.atlassian_urls",
    #"atlassian-addon-prod.fluendo.com": "fluendo.atlassian_urls",
    #"localhost": "fluendo.atlassian_urls",
}

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    },
    'jira': {
        'ENGINE': 'django_atlassian.backends.jira',
        'NAME': JIRA_SERVER,
        'USER': JIRA_USER,
        'PASSWORD': JIRA_TOKEN,
        'SECURITY': '',
    },
    'confluence': {
        'ENGINE': 'django_atlassian.backends.confluence',
        'NAME': JIRA_SERVER,
        'USER': JIRA_USER,
        'PASSWORD': JIRA_TOKEN,
        'SECURITY': '',
    },
}

DATABASE_ROUTERS = ['django_atlassian.router.Router']

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'log_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/tmp/django-DEBUG.log',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django_atlassian': {
            'handlers': ['console','log_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django_atlassian.backends.jira': {
            'handlers': ['console','log_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django_atlassian.backends.common': {
            'handlers': ['console','log_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_countries',
    'widget_tweaks',
    'django_atlassian.apps.DjangoAtlassianConfig',
    'sales.apps.SalesConfig',
    'workmodel.apps.WorkModelConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_atlassian.middleware.JWTAuthenticationMiddleware',
]

ROOT_URLCONF = 'atlassian_addon.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'atlassian_addon.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Celery related configuration
CELERY_BROKER_URL = 'redis://redis:6379'
CELERY_RESULT_BACKEND = 'django-db'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT= os.path.join(os.path.dirname(BASE_DIR), 'static_media')
