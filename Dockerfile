# Creating image based on official python3 image
FROM python:3.8.8
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

# Your contact, so can people blame you afterwards
LABEL maintainer="tech@nurturelabs.co"

ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir -p $APP_HOME
RUN mkdir -p $APP_HOME/staticfiles
WORKDIR $APP_HOME

# WORKDIR /
RUN apt-get update && apt-get install -f -y postgresql-client

# Installing svgexport
RUN apt install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_17.x | bash 
RUN apt-get install -y nodejs
RUN npm install svgexport -g
RUN apt-get install libgtk-3-0 libasound2 libnss3 xdg-utils libgbm-dev -y


# Installing all python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./

