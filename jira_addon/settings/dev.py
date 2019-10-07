import os
from .base import *

DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWD = os.environ.get('DB_PASSWD')
DB_HOST = os.environ.get('DB_HOST')

REDIS_HOST = os.environ.get('REDIS_HOST')

LDAP_NAME = os.environ.get('LDAP_NAME')
LDAP_USER = os.environ.get('LDAP_USER')
LDAP_PASSWD = os.environ.get('LDAP_PASSWD')

JIRA_SERVER = os.environ.get('JIRA_SERVER')
JIRA_USER = os.environ.get('JIRA_USER')
JIRA_TOKEN = os.environ.get('JIRA_TOKEN')

URL_BASE = os.environ.get('URL_BASE')

# Customers Server Token Auth
WEB_FLUENDO_API_SERVER = os.environ.get('WEB_FLUENDO_API_SERVER')
WEB_FLUENDO_TOKEN = os.environ.get('WEB_FLUENDO_TOKEN')

DEBUG = os.environ.get('DJANGO_DEBUG', True)


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWD,
        'HOST': DB_HOST,
        'PORT': '5432',
    },
    'ldap': {
        'ENGINE': 'ldapdb.backends.ldap',
        'NAME': LDAP_NAME,
        'USER': LDAP_USER,
        'PASSWORD': LDAP_PASSWD,
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
    #'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
]
STATIC_ROOT= os.path.join(os.path.dirname(BASE_DIR), 'static_media')
ALLOWED_HOSTS = ['*']

INSTALLED_APPS += [
    'django_atlassian.apps.DjangoAtlassianConfig',
    'atlassian.apps.AtlassianConfig',
    'debug_toolbar',
]

MIDDLEWARE += [
    'django_atlassian.middleware.JWTAuthenticationMiddleware',
    'jira_addon.middleware.multihost.MultiHostMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

HOST_MIDDLEWARE_URLCONF_MAP = {
    # The atlassian connect based app
    "jira-addon.fluendo.com": "jira_addon.atlassian_urls",
    "atlassian-addon-dev.fluendo.com": "jira_addon.atlassian_urls",
    "localhost": "jira_addon.atlassian_urls",
}

INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Celery related configuration
CELERY_BROKER_URL = 'redis://'+REDIS_HOST+':6379'
CELERY_RESULT_BACKEND = 'django-db'
