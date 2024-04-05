while read v; do
  docker build -t ametnes/nesis:"$v"-frontend . -f nesis/frontend/Dockerfile
done <version.txt