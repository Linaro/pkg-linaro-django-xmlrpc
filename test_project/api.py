from linaro_django_xmlrpc import ExposedAPI

class ExampleAPI(ExposedAPI):

    def foo(self):
        """
        Return "bar"
        """
        return "bar"
