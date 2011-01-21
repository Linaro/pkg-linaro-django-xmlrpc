# Copyright (C) 2010 Linaro Limited
#
# Author: Zygmunt Krynicki <zygmunt.krynicki@linaro.org>
#
# This file is part of Launch Control.
#
# Launch Control is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3
# as published by the Free Software Foundation
#
# Launch Control is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Launch Control.  If not, see <http://www.gnu.org/licenses/>.

"""
XML-RPC views
"""

from django.contrib.csrf.middleware import csrf_exempt
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from linaro_django_xmlrpc.models import (
    Dispatcher,
    Mapper,
    SystemAPI,
)


@csrf_exempt
def handler(request, mapper):
    """
    XML-RPC handler.

    If post data is defined, it assumes it's XML-RPC and tries to
    process as such. Empty POST request and GET requests assumes you're
    viewing from a browser and tells you about the service.
    """
    if len(request.POST):
        raw_data = request.raw_post_data
        response = HttpResponse(mimetype="application/xml")
        dispatcher = Dispatcher(mapper)
        result = dispatcher.marshalled_dispatch(raw_data)
        response.write(result)
        response['Content-length'] = str(len(response.content))
        return response
    else:
        system = SystemAPI(mapper)
        methods = [{
            'name': method,
            'signature': system.methodSignature(method),
            'help': system.methodHelp(method)}
            for method in system.listMethods()]
        return render_to_response('linaro_django_xmlrpc/api.html', {
            'methods': methods,
            'site_url': "http://{domain}".format(
                domain = Site.objects.get_current().domain)
        }, RequestContext(request))


@csrf_exempt
def default_handler(request):
    """
    Same as handler but uses default mapper
    """
    from linaro_django_xmlrpc.globals import mapper
    return handler(request, mapper)
