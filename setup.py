#!/usr/bin/env python
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


from setuptools import setup, find_packages

try:
    import versiontools
except ImportError:
    print "This package requires python-versiontools to be configured"
    print "See: http://packages.python.org/versiontools/installation.html"
    raise


import linaro_django_xmlrpc


setup(
    name='linaro-django-xmlrpc',
    version=versiontools.format_version(linaro_django_xmlrpc.__version__),
    author="Zygmunt Krynicki",
    author_email="zygmunt.krynicki@linaro.org",
    packages=find_packages(),
    url='https://launchpad.net/linaro-django-xmlrpc',
    test_suite='linaro_django_xmlrpc.test_project.tests.run_tests',
    description="Flexible XML-RPC application for Django",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Framework :: Django",
    ],
    tests_require=[
        'django-testscenarios >= 0.7.dev',
        'django-testproject >= 0.1.dev',
    ],
    setup_requires=[
        'versiontools >= 1.1',
    ],
    install_requires=[
        'Django >= 1.0',
    ],
    include_package_data=True,
)
