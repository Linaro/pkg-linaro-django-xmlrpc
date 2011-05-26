def run_tests():
    from django_testproject.tests import run_tests_for
    run_tests_for("linaro_django_xmlrpc.test_project.settings", -2)  # lest last two items in INSTALLED APPS


if __name__ == '__main__':
    run_tests()
