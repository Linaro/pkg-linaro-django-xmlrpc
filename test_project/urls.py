from django.conf.urls.defaults import patterns, url

from linaro_django_xmlrpc.views import handler
from linaro_django_xmlrpc import Mapper

from api import ExampleAPI


mapper = Mapper()
mapper.register(ExampleAPI)
mapper.register_introspection_methods()

urlpatterns = patterns('',
    url(r'^xml-rpc/',  handler, {'mapper': mapper})
)
