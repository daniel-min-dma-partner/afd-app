clear

echo ">>> Updating code base."
git fetch --all
git pull origin master

echo ">>> Updating submodules"
git submodule update

echo ">>> Removing container and image"
docker rm -f automation-web
docker rmi -f automation-web_web

echo ">>> Rebuilding image and initiating new container"
docker-compose up --build