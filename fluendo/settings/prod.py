from .base import *

DEBUG = os.environ.get('DJANGO_DEBUG', False)

FLUENDO['BASE_ADMIN_URL'] = os.environ.get(
    'FLUENDO_BASE_ADMIN_URL',
    '//fluendo.com/en/admin/'
)

ALLOWED_HOSTS = ['*']
