python .\manage.py migrate
python .\manage.py initadmin
python .\manage.py loaddata main\fixtures\system-parameter.json
python .\manage.py collectstatic --no-input --clear
python .\manage.py init-tcrm-connection