docker rm -f some-postgres
docker rmi -f postgres
docker pull postgres
docker run --publish 5432:5432 --name some-postgres -e POSTGRES_PASSWORD=mysecretpassword -d postgres
docker ps
