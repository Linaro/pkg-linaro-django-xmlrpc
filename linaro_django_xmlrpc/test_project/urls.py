from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns(
    '',
    url(r'', include('linaro_django_xmlrpc.urls')),
    url(r'^accounts/', include('django.contrib.auth.urls')),
)

