def run_tests():
    from django_testproject.tests import run_tests
    run_tests(-2)  # test last two items in INSTALLED APPS


if __name__ == '__main__':
    run_tests()
