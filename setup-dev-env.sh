#!/bin/sh
set -e
# We can either setup.py develop (--user) or just set python path ourselves.
# Since this is a standalone script the latter seems more correct.
export PYTHONPATH=$(bzr root)
LISTEN=${DJANGO_TESTPROJECT_LISTEN:-127.0.0.1:8000}
PROJECT=linaro_django_xmlrpc
echo "Setting up development environment..."
rm -f $PROJECT/test_project/test.db 
python $PROJECT/test_project/manage.py syncdb --noinput --verbosity=0
python $PROJECT/test_project/manage.py loaddata hacking_admin_user --verbosity=0
echo "Some important details":
echo " * User account:"
echo "     password: admin"
echo "     username: admin"
echo " * XML-RPC endpoint: http://$LISTEN/RPC2/"
echo " * Token manipulation: http://$LISTEN/tokens/"
echo "Starting development server..."
python $PROJECT/test_project/manage.py runserver $LISTEN --verbosity=0
