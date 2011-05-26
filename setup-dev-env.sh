#!/bin/sh
set -e
PROJECT=linaro_django_xmlrpc
rm -f $PROJECT/test_project/test.db 
python $PROJECT/test_project/manage.py syncdb --noinput
python $PROJECT/test_project/manage.py loaddata hacking_admin_user
python $PROJECT/test_project/manage.py runserver 0.0.0.0:8000
