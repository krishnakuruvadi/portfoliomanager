FROM python:3.8-slim

RUN apt-get update && apt-get install supervisor nginx vim gcc gfortran python3-dev libopenblas-dev liblapack-dev -y --no-install-recommends
COPY nginx.default /etc/nginx/sites-available/default
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

# copy source and install dependencies
RUN mkdir -p /opt/app
RUN mkdir -p /opt/app/pip_cache
RUN mkdir -p /opt/app/portfoliomanager
COPY requirements.txt start-server.sh /opt/app/
COPY src /opt/app/portfoliomanager/
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
WORKDIR /opt/app
RUN pip install -r requirements.txt --cache-dir /opt/app/pip_cache
RUN pip install gunicorn --cache-dir /opt/app/pip_cache
RUN chown -R www-data:www-data /opt/app

# Apache Tika library log file prep
RUN echo '' > /tmp/tika.log
RUN chmod 777 /tmp/tika.log

# start server
EXPOSE 8020
STOPSIGNAL SIGTERM
#CMD ["/opt/app/start-server.sh"]
#CMD ["/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf"]
CMD ["/usr/bin/supervisord"]
