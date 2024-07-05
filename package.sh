version=$1
#docker build --build-arg NESIS_VERSION="$version" -t ametnes/nesis:"$version"-api . -f nesis/api/Dockerfile
#docker build --build-arg NESIS_VERSION="$version" --build-arg PUBLIC_URL=/ --build-arg PROFILE=PROD -t ametnes/nesis:"$version"-frontend . -f nesis/frontend/Dockerfile
docker build --build-arg NESIS_VERSION="$version" -t ametnes/nesis:"$version"-rag . -f nesis/rag/Dockerfile
