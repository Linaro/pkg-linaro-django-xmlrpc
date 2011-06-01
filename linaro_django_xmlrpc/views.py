# Copyright (C) 2010, 2011 Linaro Limited
#
# Author: Zygmunt Krynicki <zygmunt.krynicki@linaro.org>
#
# This file is part of linaro-django-xmlrpc.
#
# linaro-django-xmlrpc is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3
# as published by the Free Software Foundation
#
# linaro-django-xmlrpc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with linaro-django-xmlrpc.  If not, see <http://www.gnu.org/licenses/>.

"""
XML-RPC views
"""

import base64
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.csrf.middleware import csrf_exempt
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from linaro_django_xmlrpc.models import (
    AuthToken,
    CallContext,
    Dispatcher,
    SystemAPI,
)
from linaro_django_xmlrpc.forms import AuthTokenForm


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
        dispatcher = Dispatcher(mapper)

        auth_string = request.META.get('HTTP_AUTHORIZATION')

        if auth_string is not None:
            if ' ' not in auth_string:
                return HttpResponse("Invalid HTTP_AUTHORIZATION header",status=400)
            scheme, value = auth_string.split(" ", 1)
            if scheme != "Basic":
                return HttpResponse(
                    "Unsupported HTTP_AUTHORIZATION header, only Basic scheme is supported", status=400)
            try:
                decoded_value = base64.standard_b64decode(value)
            except TypeError:
                return HttpResponse("Corrupted HTTP_AUTHORIZATION header, bad base64 encoding", status=400)
            try:
                username, secret = decoded_value.split(":", 1)
            except ValueError:
                return HttpResponse("Corrupted HTTP_AUTHORIZATION header, no user:pass", status=400)
            try:
                user = AuthToken.get_user_for_secret(username, secret)
            except Exception:
                logging.exception("bug")
            if user is None:
                response = HttpResponse("Invalid token", status=401)
                response['WWW-Authenticate'] = 'Basic relam="XML-RPC Authentication token"'
                return response
        else:
            user = None
        result = dispatcher.marshalled_dispatch(raw_data, user)
        response = HttpResponse(mimetype="application/xml")
        response.write(result)
        response['Content-length'] = str(len(response.content))
        return response
    else:
        # Split this to different view, redirect.
        # TODO: check xml-rpc spec to see what is recommended on GET requests.
        context = CallContext(user=None, mapper=mapper, dispatcher=None)
        system = SystemAPI(context)
        methods = [{
            'name': method,
            'signature': system.methodSignature(method),
            'help': system.methodHelp(method)}
            for method in system.listMethods()]
        return render_to_response('linaro_django_xmlrpc/api.html', {
            'methods': methods,
            'site_url': "http://{domain}".format(
                domain=Site.objects.get_current().domain)},
            RequestContext(request))


@csrf_exempt
def default_handler(request):
    """
    Same as handler but uses default mapper
    """
    from linaro_django_xmlrpc.globals import mapper
    return handler(request, mapper)


@login_required
def tokens(request):
    """
    List of tokens for an authenticated user
    """
    tokens = AuthToken.objects.filter(user=request.user).order_by(
        "last_used_on")
    return render_to_response(
        "linaro_django_xmlrpc/tokens.html",
        {
            "token_list": tokens,
        },
        RequestContext(request))


@login_required
def create_token(request):
    """
    Create a token for the requesting user
    """
    if request.method == "POST":
        form = AuthTokenForm(request.POST)
        if form.is_valid():
            form.save(commit=False)
            form.instance.user = request.user
            form.instance.save()
            return HttpResponseRedirect(
                reverse("linaro_django_xmlrpc.views.tokens"))
    else:
        form = AuthTokenForm()
    return render_to_response(
        "linaro_django_xmlrpc/create_token.html",
        {
            "form": form,
        },
        RequestContext(request))


@login_required
def delete_token(request, object_id):
    token = get_object_or_404(AuthToken, pk=object_id, user=request.user)
    if request.method == 'POST':
        token.delete()
        return HttpResponseRedirect(
            reverse("linaro_django_xmlrpc.views.tokens"))
    return render_to_response(
        "linaro_django_xmlrpc/authtoken_confirm_delete.html",
        {
            'token': token,
        },
        RequestContext(request))


@login_required
def edit_token(request, object_id):
    token = get_object_or_404(AuthToken, pk=object_id, user=request.user)
    if request.method == "POST":
        form = AuthTokenForm(request.POST, instance=token)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                reverse("linaro_django_xmlrpc.views.tokens"))
    else:
        form = AuthTokenForm(instance=token)
    return render_to_response(
        "linaro_django_xmlrpc/edit_token.html",
        {
            "token": token,
            "form": form,
        },
        RequestContext(request))
