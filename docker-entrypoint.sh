#!/bin/bash

echo "Migrate the Database at startup of project"

# Wait for few minute and run db migraiton
while ! python3 manage.py migrate --no-input 2>&1; do
   echo "Migration is in progress status"
   sleep 3
done

# Wait for few minute and run db fixture load
while ! python3 manage.py initadmin  2>&1; do
   echo "Admin Creation is in progress status"
   sleep 3
done

# Wait for few minute and run db fixture load
while ! python3 manage.py loaddata /home/app/web/main/fixtures/system-parameter.json  2>&1; do
   echo "Fixture is in progress status"
   sleep 3
done

# Wait for few minute and run db fixture load
while ! python3 manage.py collectstatic --no-input --clear  2>&1; do
   echo "Static Files Collection is in progress status"
   sleep 3
done

echo "Django docker is fully configured successfully."

python3 manage.py runserver 0.0.0.0:8000

exec "$@"