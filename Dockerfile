FROM python:3.9.14-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Package installations, modifications and upgrades
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
RUN pip install --upgrade pip
RUN apt-get update && apt-get install gcc gfortran ghostscript python3-dev python3-tk libopenblas-dev liblapack-dev wget unzip -y --no-install-recommends

# Create app directories
RUN mkdir -p /opt/app/portfoliomanager
RUN mkdir -p /opt/app/portfoliomanager/env_files

# App environment set up
COPY src /opt/app/portfoliomanager/
COPY env_files /opt/app/portfoliomanager/env_files/
COPY entrypoint.sh /opt/app/portfoliomanager/entrypoint.sh
COPY requirements.txt /opt/app/portfoliomanager/requirements.txt

WORKDIR /opt/app/portfoliomanager

RUN chmod +x /opt/app/portfoliomanager/entrypoint.sh
RUN pip install -r /opt/app/portfoliomanager/requirements.txt
RUN chown -R www-data:www-data /opt/app

# Apache Tika library log file prep
RUN echo '' > /tmp/tika.log
RUN chmod 777 /tmp/tika.log

# Adding Chromedriver
RUN wget https://chromedriver.storage.googleapis.com/104.0.5112.29/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip
RUN rm -f chromedriver_linux64.zip 

# Final Set up
EXPOSE 8020
STOPSIGNAL SIGTERM
ENTRYPOINT ["/opt/app/portfoliomanager/entrypoint.sh"]
