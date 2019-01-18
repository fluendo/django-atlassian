===========================
Welcome to Django-Atlassian
===========================

.. image:: https://img.shields.io/pypi/djversions/djangorestframework.svg

.. image:: https://img.shields.io/github/license/fluendo/django-atlassian.svg

.. image:: https://img.shields.io/pypi/pyversions/django-atlassian.svg


It Integrates a django project with a set of atlassian apps
such as Jira and Confluence

Installation
------------

1. Download and install using ``pip install django-atlassian``

2. Add "atlassian" to your INSTALLED_APPS setting like this::

       INSTALLED_APPS = [
            ...
            'atlassian',
       ]

3. Run `python manage.py migrate` to create the atlassian models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to add atlassian's credentials.