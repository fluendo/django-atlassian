import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
        README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-atlassian',
    version='0.1.4',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',
    description='Django app for interact with atlassian libraries such as JIRA and Confluence.',
    long_description=README,
    url='https://www.fluendo.com/',
    author='Fluendo',
    author_email='web-dev@fluendo.com',
    install_requires=[
        "Django >= 1.11",
        "PyJWT >= 1.6.4",
        "atlassian-jwt >= 1.8.1",
        "requests >= 2.18.4",
        "requests-jwt==0.5.3",
        "jira @ git+ssh://git@github.com/fluendo/jira"
    ],
    classifiers=[
            'Environment :: Web Environment',
            'Framework :: Django',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Topic :: Internet :: WWW/HTTP',
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        ],
)
