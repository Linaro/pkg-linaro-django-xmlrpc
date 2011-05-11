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
Empty module for Django to pick up this package as Django application
"""

import datetime
import inspect
import logging
import random
import xmlrpclib

from django.db import models
from django.contrib.auth.models import User
from linaro_django_xmlrpc.managers import AuthTokenManager


class AuthToken(models.Model):
    """
    Authentication token.

    Used by the AuthTokenBackend to associate a request with user.  Similar to
    OAuth resource token but much more primitive, based on HTTP Basic Auth.
    """

    # Set of valid characters for secret
    _SECRET_CHARS = "01234567890abcdefghijklmnopqrtsuwxyz"

    secret = models.CharField(
        max_length=128,
        help_text="Secret randomly generated text that grants user access instead of their regular password",
        unique=True,
        default=lambda: ''.join((random.choice(AuthToken._SECRET_CHARS) for i in xrange(128))))

    description = models.TextField(
        default="",
        help_text="Arbitrary text that helps the user to associate tokens with their intended purpose")

    created_on = models.DateTimeField(
        auto_now=True,
        help_text="Time and date when the token was created")

    last_used_on = models.DateTimeField(
        null=True,
        help_text="Time and date when the token was last used")

    user = models.ForeignKey(User, related_name="auth_tokens")

    @classmethod
    def get_user_for_secret(cls, secret):
        """
        Lookup an user for this secret, returns None on failure.

        This also bumps last_used_on if successful
        """
        try:
            token = cls.objects.get(secret=secret)
            token.last_used_on = datetime.datetime.utcnow()
            return token.user
        except cls.DoesNotExist:
            return None


def xml_rpc_signature(*sig):
    """
    Small helper that attaches "xml_rpc_signature" attribute to the
    function. The attribute is a list of values that is then reported
    by system_methodSignature().

    This is a simplification of the XML-RPC spec that allows to attach a
    list of variants (like I may accept this set of arguments, or that
    set or that other one). This version has only one set of arguments.

    Note that it's a purely presentational argument for our
    implementation. Putting bogus values here won't spoil the day.

    The first element is the signature of the return type.
    """
    def decorator(func):
        func.xml_rpc_signature = list(sig)
        return func
    return decorator


class FaultCodes(object):
    """
    Common fault codes.

    See: http://xmlrpc-epi.sourceforge.net/specs/rfc.fault_codes.php
    """
    class ParseError:
        NOT_WELL_FORMED = -32700
        UNSUPPORTED_ENCODING = -32701
        INVALID_CHARACTER_FOR_ENCODING = -32702
    class ServerError:
        INVALID_XML_RPC = -32600
        REQUESTED_METHOD_NOT_FOUND = -32601
        INVALID_METHOD_PARAMETERS = -32602
        INTERNAL_XML_RPC_ERROR = -32603
    APPLICATION_ERROR = -32500
    SYSTEM_ERROR = -32400
    TRANSPORT_ERROR = -32300


class ExposedAPI(object):
    """
    Base class for exposing code via XML-RPC.

    To use inherit from this class and add public methods (not prefixed
    with _). Each method should have a sensible docstring as it will be
    exposed to developers accessing your services.

    To work with authentication you can inspect the _user instance
    variable. If the request was authenticated using any available
    authentication method the instance variable will point to a
    django.contrib.auth.models.User instance. You will _never_ get
    AnonymousUser or users with is_active=False, those are replaced by
    None automatically.
    """

    def __init__(self, user=None):
        if user is not None and user.is_authenticated() and user.is_active:
            self._user = user
        else:
            self._user = None


class Mapper(object):
    """
    Simple namespace for mapping multiple subclasses of ExposedAPI
    subclasses using one dispatcher.

    >>> class Hello(ExposedAPI):
    ...     def world(self):
    ...         return "hi"

    The mapper is then used by dispatcher to lookup methods.
    >>> mapper = Mapper()
    >>> mapper.register(Hello)

    The lookup method allows to get callable thing matching the
    specified XML-RPC method name.
    >>> func = mapper.lookup('Hello.world')
    >>> func()
    "hi"
    """

    def __init__(self):
        self.registered = {}

    def register(self, obj_or_cls, name=None):
        """
        Expose specified object or class under specified name

        Name defaults to the name of the class.
        """
        if name is None:
            if isinstance(obj_or_cls, type):
                name = obj_or_cls.__name__
            else:
                name = obj_or_cls.__class__.__name__
        self.registered[name] = obj_or_cls

    def lookup(self, name, user=None):
        """
        Lookup the callable associated with th specified name.

        The callable is a bound method of a registered object or a bound
        method of a freshly instantiated object of a registered class.

        The optional argument user is passed to the class constructor. If the
        specified method name belongs to a registered object user identity
        information is not available.

        @return A callable or None if the name does not designate any
        registered entity.
        """
        if "." in name:
            api_name, meth_name = name.split('.', 1)
        else:
            meth_name = name
            api_name = ''
        if meth_name.startswith("_"):
            return
        obj_or_cls = self.registered.get(api_name)
        if obj_or_cls is None:
            return
        try:
            if isinstance(obj_or_cls, type):
                obj = obj_or_cls(user)
            else:
                obj = obj_or_cls
        except:
            # TODO: Perhaps this should be an APPLICATION_ERROR?
            logging.exception("unable to instantiate stuff")
        meth = getattr(obj, meth_name, None)
        if not inspect.ismethod(meth):
            return
        return meth

    def list_methods(self):
        """
        Calculate a sorted list of registered methods.

        Each method is exposed either from the root object or from a single
        level hierarchy of named objects. For example:

        'system.listMethods' is a method exposed from the 'system' object
        'version' is a method exposed from the root object.

        @return A list of sorted method names
        """
        methods = []
        for register_path in self.registered:
            cls = self.registered[register_path]
            for method_name, impl in inspect.getmembers(
                cls, inspect.ismethod):
                if method_name.startswith("_"):
                    continue
                if register_path:
                    methods.append(register_path + "." + method_name)
                else:
                    methods.append(method_name)
        methods.sort()
        return methods

    def register_introspection_methods(self):
        """
        Register SystemAPI instance as 'system' object.

        This method is similar to the SimpleXMLRPCServer method with the same
        name. It exposes several standard XML-RPC methods that make it
        possible to introspect all exposed methods.

        For reference see the SystemAPI class.
        """
        self.register(SystemAPI(self), 'system')


class Dispatcher(object):
    """
    XML-RPC dispatcher based on Mapper (for name lookup) and libxmlrpc (for
    marshalling). The API is loosely modeled after SimpleXMLRPCDispatcher from
    the standard python library but methods are not private and take
    additional arguments that allow for user authentication.

    Unlike the original server this server does not expose errors in the
    internal method implementation unless those errors are raised as
    xmlrpclib.Fault instances.

    Subclasses may want to override handle_internal_error() that currently
    uses logging.exception to print as short message.
    """

    def __init__(self, mapper, allow_none=True):
        self.mapper = mapper
        self.allow_none = allow_none

    def decode_request(self, data):
        """
        Decode marshalled XML-RPC message.

        @return A tuple with (method_name, params)
        """
        # TODO: Check that xmlrpclib.loads can only raise this exception (it
        # probably can raise some others as well but this is not documented) and
        # handle each by wrapping it into an appropriate Fault with correct
        # code/message.
        try:
            params, method_name = xmlrpclib.loads(data)
            return method_name, params
        except xmlrpclib.ResponseError:
            raise xmlrpclib.Fault(
                FaultCodes.ServerError.INVALID_XML_RPC,
                "Unable to decode request")
        except:
            raise xmlrpclib.Fault(
                FaultCodes.ServerError.INTERNAL_XML_RPC_ERROR,
                "Unable to decode request")

    def marshalled_dispatch(self, data, user=None):
        """
        Dispatch marshalled request (encoded with XML-RPC envelope).

        Returns the text of the response
        """
        try:
            method, params = self.decode_request(data)
            response = self.dispatch(method, params, user)
        except xmlrpclib.Fault as fault:
            # Push XML-RPC faults to the client
            response = xmlrpclib.dumps(
                fault, allow_none=self.allow_none)
        else:
            # Package responses and send them to the client
            response = (response,)
            response = xmlrpclib.dumps(
                response, methodresponse=1, allow_none=self.allow_none)
        return response

    def dispatch(self, method, params, user=None):
        """
        Dispatch method with specified parameters
        """
        try:
            impl = self.mapper.lookup(method, user)
            if impl is None:
                raise xmlrpclib.Fault(
                        FaultCodes.ServerError.REQUESTED_METHOD_NOT_FOUND,
                        "No such method: %r" % method)
                # TODO: check parameter types before calling
            return impl(*params)
        except xmlrpclib.Fault:
            # Forward XML-RPC Faults to the client
            raise
        except:
            # Treat all other exceptions as internal errors 
            self.handle_internal_error(method, params)
            raise xmlrpclib.Fault(
                FaultCodes.ServerError.INTERNAL_XML_RPC_ERROR,
                "Internal Server Error")

    def handle_internal_error(self, method, params):
        """
        Handle exceptions raised while dispatching registered methods.

        Subclasses may implement this but cannot prevent the
        xmlrpclib.Fault from being raised.
        """
        logging.exception(
            "Unable to dispatch XML-RPC method %s(%s)",
            method, params)


class SystemAPI(object):
    """
    XML-RPC System API

    This API may be mapped as "system" object to conform to XML-RPC
    introspection specification. When doing so make sure to map an _instance_
    and not the class as SystemAPI needs access to the mapper.
    """
    #TODO: Implement and expose system.getCapabilities() and advertise
    #      support for standardised fault codes.
    #      See: http://tech.groups.yahoo.com/group/xml-rpc/message/2897

    def __init__(self, mapper):
        self.mapper = mapper

    def listMethods(self):
        return self.mapper.list_methods()

    def methodSignature(self, method_name):
        impl = self.mapper.lookup(method_name)
        if impl is None:
            return ""
        # When signature is not known return "undef"
        # See: http://xmlrpc-c.sourceforge.net/introspection.html
        return getattr(impl, 'xml_rpc_signature', "undef")

    @xml_rpc_signature('str', 'str')
    def methodHelp(self, method_name):
        """
        Return documentation for specified method
        """
        impl = self.mapper.lookup(method_name)
        if impl is None:
            return ""
        else:
            import pydoc
            return pydoc.getdoc(impl)
