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
Unit tests for Linaro Django XML-RPC Application
"""
import re
import xmlrpclib

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django_testscenarios.ubertest import TestCase

from linaro_django_xmlrpc.models import (
    AuthToken,
    Dispatcher,
    ExposedAPI,
    FaultCodes,
    Mapper,
    SystemAPI,
    xml_rpc_signature,
)


class MockUser(object):
    """
    Mock django.contrib.auth.models.User class for out test cases
    """

    def __init__(self, is_authenticated, is_active):
        self._is_active = is_active
        self._is_authenticated = is_authenticated

    @property
    def is_active(self):
        return self._is_active

    def is_authenticated(self):
        return self._is_authenticated


class ExampleAPI(ExposedAPI):
    """
    Fake API for our tests
    """

    @xml_rpc_signature("str")
    def foo(self):
        """foo docstring"""
        return "bar"

    def bar(self):
        return "foo"


class ExposedAPITests(TestCase):

    def test_user_defaults_to_None(self):
        api = ExposedAPI()
        self.assertEqual(api._user, None)

    def test_unauthenticated_users_are_ignored(self):
        user = MockUser(is_authenticated=False, is_active=True)
        api = ExposedAPI(user)
        self.assertEqual(api._user, None)

    def test_inactive_users_are_ignored(self):
        user = MockUser(is_authenticated=True, is_active=False)
        api = ExposedAPI(user)
        self.assertEqual(api._user, None)

    def test_authenticated_active_users_are_allowed(self):
        user = MockUser(is_authenticated=True, is_active=True)
        api = ExposedAPI(user)
        self.assertEqual(api._user, user)


class MapperTests(TestCase):

    def setUp(self):
        super(MapperTests, self).setUp()
        self.mapper = Mapper()

    def test_register_guesses_class_name(self):
        self.mapper.register(ExampleAPI)
        self.assertTrue("ExampleAPI" in self.mapper.registered)

    def test_register_guesses_object_name(self):
        self.mapper.register(ExampleAPI())
        self.assertTrue("ExampleAPI" in self.mapper.registered)

    def test_register_respects_explicit_class_name(self):
        self.mapper.register(ExampleAPI, "example_api")
        self.assertTrue("example_api" in self.mapper.registered)

    def test_register_overwrites_previous_binding(self):
        class TestAPI1(ExposedAPI):
            pass
        class TestAPI2(ExposedAPI):
            pass
        self.mapper.register(TestAPI1, 'API')
        self.mapper.register(TestAPI2, 'API')
        self.assertTrue('API' in self.mapper.registered)
        self.assertTrue(self.mapper.registered['API'] is TestAPI2)

    def test_lookup_finds_method(self):
        self.mapper.register(ExampleAPI)
        foo = self.mapper.lookup("ExampleAPI.foo")
        # Calling the method is easier than doing some other magic here
        self.assertEqual(foo(), "bar")

    def test_lookup_finds_method_in_root_scope(self):
        self.mapper.register(ExampleAPI, '')
        foo = self.mapper.lookup("foo")
        # Calling the method is easier than doing some other magic here
        self.assertEqual(foo(), "bar")

    def test_lookup_returns_none_if_method_not_found(self):
        self.mapper.register(ExampleAPI)
        retval = self.mapper.lookup("ExampleAPI.missing_method")
        self.assertEqual(retval, None)

    def test_lookup_returns_none_if_object_or_class_not_found(self):
        retval = self.mapper.lookup("ExampleAPI.foo")
        self.assertEqual(retval, None)

    def test_list_methods_without_methods(self):
        class TestAPI(ExposedAPI):
            pass
        self.mapper.register(TestAPI)
        retval = self.mapper.list_methods()
        self.assertEqual(retval, [])

    def test_list_methods_from_global_scope(self):
        class TestAPI(ExposedAPI):
            def a(self):
                pass
            def b(self):
                pass
            def c(self):
                pass
        self.mapper.register(TestAPI, '')
        retval = self.mapper.list_methods()
        self.assertEqual(retval, ['a', 'b', 'c'])

    def test_list_methods_from_class_scope(self):
        class TestAPI(ExposedAPI):
            def a(self):
                pass
            def b(self):
                pass
            def c(self):
                pass
        self.mapper.register(TestAPI)
        retval = self.mapper.list_methods()
        self.assertEqual(retval, ['TestAPI.a', 'TestAPI.b', 'TestAPI.c'])

    def test_list_methods_from_object_scope(self):
        class TestAPI(ExposedAPI):
            def a(self):
                pass
            def b(self):
                pass
            def c(self):
                pass
        self.mapper.register(TestAPI())
        retval = self.mapper.list_methods()
        self.assertEqual(retval, ['TestAPI.a', 'TestAPI.b', 'TestAPI.c'])

    def test_list_methods_with_two_sources(self):
        class SourceA(ExposedAPI):
            def a(self):
                pass
        class SourceB(ExposedAPI):
            def a(self):
                pass
        self.mapper.register(SourceA)
        self.mapper.register(SourceB)
        retval = self.mapper.list_methods()
        self.assertEqual(retval, ['SourceA.a', 'SourceB.a'])


class TestAPI(ExposedAPI):
    """
    Test API that gets exposed by the dispatcher for test runs.
    """

    def ping(self):
        """
        Return "pong" message
        """
        return "pong"

    def echo(self, arg):
        """
        Return the argument back to the caller
        """
        return arg

    def boom(self, code, string):
        """
        Raise a Fault exception with the specified code and string
        """
        raise xmlrpclib.Fault(code, string)

    def internal_boom(self):
        """
        Raise a regular python exception (this should be hidden behind
        an internal error fault)
        """
        raise Exception("internal boom")


class DispatcherTests(TestCase):

    def setUp(self):
        super(DispatcherTests, self).setUp()
        self.mapper = Mapper()
        self.mapper.register(TestAPI, '')
        self.dispatcher = Dispatcher(self.mapper)

    def xml_rpc_call(self, method, *args):
        """
        Perform XML-RPC call on our internal dispatcher instance

        This calls the method just like we would have normally from our view.
        All arguments are marshaled and un-marshaled. XML-RPC fault exceptions
        are raised like normal python exceptions (by xmlrpclib.loads)
        """
        request = xmlrpclib.dumps(tuple(args), methodname=method)
        response = self.dispatcher.marshalled_dispatch(request)
        # This returns return value wrapped in a tuple and method name
        # (which we don't have here as this is a response message).
        return xmlrpclib.loads(response)[0][0]

    def test_standard_fault_code_for_method_not_found(self):
        try:
            self.xml_rpc_call("method_that_does_not_exist")
        except xmlrpclib.Fault as ex:
            self.assertEqual(
                ex.faultCode,
                FaultCodes.ServerError.REQUESTED_METHOD_NOT_FOUND)
        else:
            self.fail("Calling missing method did not raise an exception")

    def test_internal_error_handler_is_called_on_exception(self):
        def handler(method, params):
            self.assertEqual(method, 'internal_boom')
            self.assertEqual(params, ())
        self.dispatcher.handle_internal_error = handler
        try:
            self.xml_rpc_call("internal_boom")
        except xmlrpclib.Fault:
            pass
        else:
            self.fail("Exception not raised")

    def test_standard_fault_code_for_internal_error(self):
        # This handler is here just to prevent the default one from
        # spamming the console with the error that is raised inside the
        # internal_boom() method
        self.dispatcher.handle_internal_error = lambda method, args: None
        try:
            self.xml_rpc_call("internal_boom")
        except xmlrpclib.Fault as ex:
            self.assertEqual(
                ex.faultCode,
                FaultCodes.ServerError.INTERNAL_XML_RPC_ERROR)
        else:
            self.fail("Exception not raised")

    def test_ping(self):
        retval = self.xml_rpc_call("ping")
        self.assertEqual(retval, "pong")

    def test_echo(self):
        self.assertEqual(self.xml_rpc_call("echo", 1), 1)
        self.assertEqual(self.xml_rpc_call("echo", "string"), "string")
        self.assertEqual(self.xml_rpc_call("echo", 1.5), 1.5)

    def test_boom(self):
        self.assertRaises(xmlrpclib.Fault,
                self.xml_rpc_call, "boom", 1, "str")


class SystemAPITest(TestCase):

    def setUp(self):
        super(SystemAPITest, self).setUp()
        self.mapper = Mapper()
        self.system_api = SystemAPI(self.mapper)

    def test_listMethods_just_calls_mapper_list_methods(self):
        obj = object()
        self.mapper.list_methods = lambda: obj
        retval = self.system_api.listMethods()
        self.assertEqual(retval, obj)

    def test_methodHelp_returns_blank_when_method_has_no_docstring(self):
        class TestAPI(ExposedAPI):
            def method(self):
                pass
        self.mapper.register(TestAPI)
        retval = self.system_api.methodHelp("TestAPI.method")
        self.assertEqual(retval, "")

    def test_methodHelp_returns_the_docstring(self):
        class TestAPI(ExposedAPI):
            def method(self):
                """docstring"""
        self.mapper.register(TestAPI)
        retval = self.system_api.methodHelp("TestAPI.method")
        self.assertEqual(retval, "docstring")

    def test_methodHelp_strips_the_leading_whitespce(self):
        class TestAPI(ExposedAPI):
            def method(self):
                """
                line 1
                line 2
                """
        self.mapper.register(TestAPI)
        retval = self.system_api.methodHelp("TestAPI.method")
        self.assertEqual(retval, "line 1\nline 2")

    def test_methodSignature_returns_undef_by_default(self):
        class TestAPI(ExposedAPI):
            def method(self):
                pass
        self.mapper.register(TestAPI)
        retval = self.system_api.methodSignature("TestAPI.method")
        self.assertEqual(retval, 'undef')

    def test_methodSignature_returns_signature_when_defined(self):
        class TestAPI(ExposedAPI):
            @xml_rpc_signature('str', 'int')
            def int_to_str(value):
                return "%s" % value
        self.mapper.register(TestAPI)
        retval = self.system_api.methodSignature("TestAPI.int_to_str")
        self.assertEqual(retval, ['str', 'int'])


class HandlerTests(TestCase):

    urls = 'linaro_django_xmlrpc.urls'

    def setUp(self):
        super(HandlerTests, self).setUp()
        self.url = reverse("linaro_django_xmlrpc.views.default_handler")
        from linaro_django_xmlrpc.globals import mapper
        self.mapper = mapper

    def test_handler_get_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_request_context_was_used(self):
        response = self.client.get(self.url)
        self.assertTrue(
            isinstance(response.context, RequestContext))

    def test_get_request_shows_help(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "linaro_django_xmlrpc/api.html")

    def test_empty_post_request_shows_help(self):
        response = self.client.post(self.url)
        self.assertTemplateUsed(response, "linaro_django_xmlrpc/api.html")

    def test_help_page_lists_all_methods(self):
        response = self.client.get("/xml-rpc/")
        for method_name in self.mapper.list_methods():
            self.assertIn(
                method_name,
                [method["name"] for method in response.context['methods']]
            )


class AuthTokenTests(TestCase):

    _USER = "user"
    _INEXISTING_SECRET = "inexisting-secret"

    def setUp(self):
        super(AuthTokenTests, self).setUp()
        self.user = User.objects.get_or_create(username=self._USER)[0]

    def test_secret_is_generated(self):
        token = AuthToken.objects.create(user=self.user)
        self.assertTrue(re.match("[a-z0-9]{128}", token.secret))

    def test_generated_secret_is_not_constant(self):
        token1 = AuthToken.objects.create(user=self.user)
        token2 = AuthToken.objects.create(user=self.user)
        self.assertNotEqual(token1.secret, token2.secret)

    def test_created_on(self):
        token = AuthToken.objects.create(user=self.user)
        self.assertTrue(token.created_on != None)
        # XXX: How to sensibly test auto_now? aka how to mock time

    def test_last_used_on_is_initially_empty(self):
        token = AuthToken.objects.create(user=self.user)
        self.assertTrue(token.last_used_on is None)
    
    def test_lookup_user_for_secret_returns_none_on_failure(self):
        user = AuthToken.get_user_for_secret(self._INEXISTING_SECRET)
        self.assertTrue(user is None)

    def test_get_user_for_secret(self):
        token = AuthToken.objects.create(user=self.user)
        user = AuthToken.get_user_for_secret(token.secret)
        self.assertEqual(user, self.user)
