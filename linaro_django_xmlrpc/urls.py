from django.conf.urls.defaults import patterns, url

from linaro_django_xmlrpc.views import handler
from linaro_django_xmlrpc import Mapper

mapper = Mapper()
mapper.register_introspection_methods()

urlpatterns = patterns(
    '',
    url(r'^xml-rpc/',
        view=handler,
        kwargs={'mapper': mapper},
        name='linaro_django_xmlrpc.views.handler'),
)
