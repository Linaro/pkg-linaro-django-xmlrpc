import sys
import os

# Add this directory to path so that 'example' can be imported later
# below. Without this the runner will fail when started via ``setup.py
# test``
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from django_testproject.settings import gen_settings

locals().update(
    gen_settings(
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sites',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'linaro_django_xmlrpc',
            'example',
        ],
        ROOT_URLCONF = 'test_project.urls',
        )
    )
