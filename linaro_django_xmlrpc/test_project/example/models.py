from linaro_django_xmlrpc.models import ExposedAPI
from linaro_django_xmlrpc.globals import mapper


class ExampleAPI(ExposedAPI):

    def foo(self):
        """
        Return "bar"
        """
        return "bar"


# Map our class in the default global mapper
mapper.register(ExampleAPI)
