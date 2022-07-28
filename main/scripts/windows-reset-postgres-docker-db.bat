docker exec -it some-postgres echo "==== DROP DATABASE ===="
docker exec -it some-postgres psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS tcrm_db;"
docker exec -it some-postgres psql -U postgres -d postgres -c "DROP ROLE IF EXISTS tcrm_user;"

docker exec -it some-postgres echo ""

docker exec -it some-postgres echo "==== CREATE DATABASE ===="
docker exec -it some-postgres psql -U postgres -d postgres -c "CREATE DATABASE tcrm_db;"

docker exec -it some-postgres psql -U postgres -d postgres -c "CREATE USER tcrm_user WITH PASSWORD '7YjvxvWLC8';"
docker exec -it some-postgres psql -U postgres -d postgres -c "ALTER ROLE tcrm_user SET client_encoding TO 'utf8';"
docker exec -it some-postgres psql -U postgres -d postgres -c "ALTER ROLE tcrm_user SET default_transaction_isolation TO 'read committed';"
docker exec -it some-postgres psql -U postgres -d postgres -c "ALTER ROLE tcrm_user SET timezone TO 'UTC';"
docker exec -it some-postgres psql -U postgres -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE tcrm_db TO tcrm_user;"

docker exec -it some-postgres echo ""

docker exec -it some-postgres echo "==== SHOW CONFIGURATIONS ===="
docker exec -it some-postgres psql -U postgres -d postgres -c "\l"
docker exec -it some-postgres psql -U postgres -d postgres -c "\du"
docker exec -it some-postgres psql -U postgres -d postgres -c "\z tcrm_db"

docker exec -it some-postgres echo ""

echo "RUN the following commands manually"
echo "Set-ExecutionPolicy Unrestricted -Scope Process"
