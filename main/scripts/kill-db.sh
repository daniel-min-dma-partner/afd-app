#export me=$(whoami)
#echo "==== CAPTURING CURRENT SYS USER ===="
#echo $me
#
#echo ""
#
#echo "==== DROP DATABASE ===="
#psql -U $me -d postgres -c "DROP DATABASE IF EXISTS tcrm_db;"
#psql -U $me -d postgres -c "DROP ROLE IF EXISTS tcrm_user;"
#
#echo ""
#
#echo "==== CREATE DATABASE ===="
#psql -U $me -d postgres -c "CREATE DATABASE tcrm_db;"
#
#psql -U $me -d postgres -c "CREATE USER tcrm_user WITH PASSWORD '7YjvxvWLC8';"
#psql -U $me -d postgres -c "ALTER ROLE tcrm_user SET client_encoding TO 'utf8';"
#psql -U $me -d postgres -c "ALTER ROLE tcrm_user SET default_transaction_isolation TO 'read committed';"
#psql -U $me -d postgres -c "ALTER ROLE tcrm_user SET timezone TO 'UTC';"
#psql -U $me -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE tcrm_db TO tcrm_user;"
#
#echo ""
#
#echo "==== SHOW CONFIGURATIONS ===="
#psql -U $me -d postgres -c "\l"
#psql -U $me -d postgres -c "\du"
#psql -U $me -d postgres -c "\z tcrm_db"
#
#echo ""
#
#echo "==== BUILD DATABASE ===="
#python manage.py makemigrations
#python manage.py migrate
#python manage.py initadmin
#
#echo ""
#
#echo "==== UNSETTING EXPORTED ENV VAR 'me' ===="
#unset me
#echo $me
#
#echo "==== END ===="