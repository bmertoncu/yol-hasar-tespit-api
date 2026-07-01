docker kurma: docker build -t yol-hasar-api
docker çalıştırma: docker run -p 8000:8000 -v "$(pwd):/app" yol-hasar-api