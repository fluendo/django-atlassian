Example Configuration
---------------------
Backend mode
~~~~~~~~~~~~

.. code-block:: python

    DATABASES = {
        'jira': {
            'ENGINE': 'django_atlassian.backends.jira',
            'NAME': 'https://your-site.atlassian.net',
            'USER': '', # Your user
            'PASSWORD': '', # Your password
            'SECURITY': '',
        },

    DATABASE_ROUTERS = ['django_atlassian.router.Router']

Application mode
~~~~~~~~~~~~~~~~

In this mode, you setup a database configuration to connect to a specific Jira/Confluence
cloud instance. All custom fields will be automatically introspected.

Setup the router to make the connected host model be accessed through their own database:

.. code-block:: python

    DATABASE_ROUTERS = ['django_atlassian.router.Router']

    ALLOWED_HOSTS = ['<ID>.ngrok.io']


Create a basic ``atlassian-connect.json`` template file:

.. code-block:: json

    {
        "name": "<Your app name>",
        "description": "<Your app description>",
        "key": "<Your app private key>",
        "baseUrl": "<Your host set on ALLOWED_HOSTS>",
        "vendor": {
            "name": "<Your company>",
            "url": "<Your website>",
        },
        "authentication": {
            "type": "jwt"
        },
        "lifecycle": {
            "installed": "{% url 'django-atlassian-installed' %}"
        },
        "scopes": [
            "read", "write"
        ],
        "apiVersion": 1,
        "modules": {
        }
    }