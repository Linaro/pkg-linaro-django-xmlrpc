from django.conf.urls.defaults import patterns, url

from linaro_django_xmlrpc.views import handler
from linaro_django_xmlrpc.globals import mapper

urlpatterns = patterns(
    '',
    url(r'^xml-rpc/',
        view=handler,
        kwargs={'mapper': mapper},
        name='linaro_django_xmlrpc.views.handler'),
)
