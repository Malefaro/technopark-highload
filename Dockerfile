FROM python:3.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /opt/server
WORKDIR /opt/server
COPY . /opt/server/
EXPOSE 3000
CMD python src/main.py