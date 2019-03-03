#FROM python:3.7
#ENV PYTHONUNBUFFERED 1
#RUN mkdir /opt/server
#WORKDIR /opt/server
#COPY . /opt/server/
#EXPOSE 3000
#CMD python src/main.py

FROM ubuntu:18.04
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install python3
ENV PYTHONUNBUFFERED 1
RUN mkdir /opt/server
WORKDIR /opt/server
COPY . /opt/server/
EXPOSE 80
CMD python3 src/main.py