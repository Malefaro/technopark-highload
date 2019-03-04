# Python web-server

Web-server based on epoll and coroutines

Config file spec:
```
cpu_limit 2
document_root /var/www/html
port 80
```

Install:
```
git clone https://github.com/Malefaro/technopark-highload
technopark-highload

docker build -t technopark-highload .
docker run -p 80:80 -v ./httpd.conf:/etc/httpd.conf:ro -v ./http-test-suite:/var/www/html:ro --name technopark-highload -t technopark-highload
```
Or via docker-compose:
```
docker-compose build
docker-compose up --build
```