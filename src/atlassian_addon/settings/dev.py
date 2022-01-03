import os
from .base import *

DEBUG = os.environ.get('DJANGO_DEBUG', True)

FLUENDO['BASE_ADMIN_URL'] = os.environ.get(
    'FLUENDO_BASE_ADMIN_URL',
    '//localhost:8000/en/admin/'
)

ALLOWED_HOSTS = ['*']

INSTALLED_APPS += [
    'debug_toolbar',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = ['127.0.0.1', 'localhost']
