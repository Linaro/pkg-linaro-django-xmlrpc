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
            'django.contrib.messages',
            'django_testproject',
            'linaro_django_xmlrpc',
            'example',
        ],
        MIDDLEWARE_CLASSES=[
            'django.contrib.messages.middleware.MessageMiddleware',
        ],
        TEMPLATE_LOADERS=[
            'django.template.loaders.eggs.Loader'
        ],
        ROOT_URLCONF='linaro_django_xmlrpc.test_project.urls',
    )
)
