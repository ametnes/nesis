while read -r v; do
  docker build -t ametnes/nesis:"$v"-rag . -f nesis/rag/Dockerfile
  docker build -t ametnes/nesis:"$v"-api . -f nesis/api/Dockerfile
  docker build --build-arg PUBLIC_URL=/ --build-arg PROFILE=PROD -t ametnes/nesis:"$v"-frontend . -f nesis/frontend/Dockerfile
done <version.txt
