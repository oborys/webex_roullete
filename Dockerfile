FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.7
RUN apk --update add bash nano
ENV STATIC_URL /static
ENV STATIC_PATH /var/www/app/static
ENV TZ Europe/Kiev
COPY ./requirements.txt /var/www/requirements.txt
COPY ./app/static /var/www/app/static
RUN pip install -r /var/www/requirements.txt
