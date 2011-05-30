#!/usr/bin/env python
from django.core.management import execute_manager
try:
    from linaro_django_xmlrpc.test_project import settings
except ImportError as ex:
    import logging
    logging.exception("Unable to import application settings")
    raise SystemExit(ex)

if __name__ == "__main__":
    execute_manager(settings)
