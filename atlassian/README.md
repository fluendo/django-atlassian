Django based Atlassian Connect 
==============================
django-atlassian allows you to build a Atlassian Connect apps using Django, it includes:
+ JWT support
+ Jira's django db backend
+ Confluence's django db backend


Installation
------------
Install the package with pip:
```
$ pip install django-atlassian
```

Example Configuration
---------------------
### Backend mode
In this mode, you setup a database configuration to connect to a specific Jira/Confluence
cloud instance. All custom fields will be automatically introspected.

```python
DATABASES = {
    'jira': {
        'ENGINE': 'django_atlassian.backends.jira',
        'NAME': 'https://your-site.atlassian.net',
        'USER': '', # Your user
        'PASSWORD': '', # Your password
        'SECURITY': '',
    },

DATABASE_ROUTERS = ['django_atlassian.router.Router']
```

### Application mode
In this mode, once some Jira/Confluence clound instance connects to your app, it will be
automatically registered and the corresponding Jira's Issue model generated. The connected
host information will be stored on your default database.

Setup the router to make the connected host model be accessed through their own database:
```python
DATABASE_ROUTERS = ['django_atlassian.router.Router']

ALLOWED_HOSTS = ['<ID>.ngrok.io']
```

Create a basic `atlassian-connect.json` template file:
```json
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
```

Contributing
------------
If you'd like to contribute, the best approach is to send a well-formed pull
request, complete with tests and documentation. Pull requests should be
focused: trying to do more than one thing in a single request will make it more
difficult to process.

References
----------
Database implementation:
https://simpleisbetterthancomplex.com/media/2016/11/db.pdf

Dynamic model field injection:
http://blog.jupo.org/2011/11/10/django-model-field-injection/
https://github.com/Zagrebelin/smyt_test/tree/master/msyt
https://code.djangoproject.com/wiki/DynamicModels
http://lazypython.blogspot.com/2008/11/django-models-digging-little-deeper.html
https://code.djangoproject.com/ticket/22555
https://stackoverflow.com/questions/2357528/explanation-of-contribute-to-class
https://code.djangoproject.com/wiki/DevModelCreation
