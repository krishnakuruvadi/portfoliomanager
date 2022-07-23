FROM python:3.8-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Package installations, modifications and upgrades
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
RUN pip install --upgrade pip
RUN apt-get update && apt-get install gcc gfortran python3-dev libopenblas-dev liblapack-dev -y --no-install-recommends

# Create app directories
RUN mkdir -p /opt/app/portfoliomanager

# App environment set up
COPY src /opt/app/portfoliomanager/
COPY dev-requirements.txt /opt/app/portfoliomanager/dev-requirements.txt
WORKDIR /opt/app/portfoliomanager

RUN chmod +x /opt/app/portfoliomanager/dev-entrypoint.sh
RUN pip install -r /opt/app/portfoliomanager/dev-requirements.txt
RUN chown -R www-data:www-data /opt/app

# Apache Tika library log file prep
RUN echo '' > /tmp/tika.log
RUN chmod 777 /tmp/tika.log

# Final Set up
EXPOSE 8020
STOPSIGNAL SIGTERM
ENTRYPOINT ["/opt/app/portfoliomanager/dev-entrypoint.sh"]
