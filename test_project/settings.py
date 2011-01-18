from django_testproject.settings import gen_settings


locals().update(
    gen_settings(
        INSTALLED_APPS=[
            'django.contrib.sites',
            'linaro_django_xmlrpc',
        ],
        ROOT_URLCONF = 'test_project.urls'
    )
)
