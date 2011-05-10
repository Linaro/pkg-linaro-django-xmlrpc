#!/usr/bin/env python
#
# Copyright (C) 2010 Linaro Limited
#
# Author: Zygmunt Krynicki <zygmunt.krynicki@linaro.org>
#
# This file is part of Launch Control.
#
# Launch Control is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# as published by the Free Software Foundation
#
# Launch Control is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Launch Control.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages

from linaro_django_xmlrpc import __version__

setup(
    name='linaro-django-xmlrpc',
    version=str(__version__),
    author="Zygmunt Krynicki",
    author_email="zygmunt.krynicki@linaro.org",
    packages=find_packages(),
    url='https://launchpad.net/linaro-django-xmlrpc',
    test_suite='test_project.tests.run_tests',
    description="Flexible XML-RPC application for Django",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Framework :: Django",
    ],
    data_files=[
        ('linaro_django_xmlrpc/templates/linaro_django_xmlrpc',
         ['linaro_django_xmlrpc/templates/linaro_django_xmlrpc/api.html'])
    ],
    tests_require=[
        'django-testscenarios >= 0.5.2',
    ],
    setup_requires=[
        'versiontools >= 1.0.2',
    ],
    install_requires=[
        'Django >= 1.0',
        'versiontools >= 1.0.2',
    ],
)
