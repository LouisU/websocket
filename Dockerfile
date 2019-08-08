FROM python:3.7.3
# part 1
# LABAL
# ENV
COPY . /var/www/websocket
WORKDIR /var/www/websocket

# part 2 install dependency of project
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 5000


# sudo docker run -d --name nginx -p 4433:443 --network louis-ns -v /gcg/certificates:/etc/certificates -v /home/louis/example/nginx.conf:/etc/nginx/nginx.conf nginx
# sudo docker run --name websocket -d --network louis-ns 1056699051/websocket  python app.py