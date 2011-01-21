from django.conf.urls.defaults import patterns, url

from linaro_django_xmlrpc.views import default_handler


urlpatterns = patterns(
    '',
    url(r'^xml-rpc/', default_handler,
        name='linaro_django_xmlrpc.views.default_handler'),
)
