FROM python:3.8-slim-buster

WORKDIR /app

ENV MQTT_BROKER=0.0.0.0 \
    MQTT_PORT=1883\    
    MQTT_USERNAME=username\
    MQTT_PASSWORD=password\
    MQTT_PREFIX=syslog\
    MQTT_VERBOSE=0\
    PYTHONUNBUFFERED=1

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

WORKDIR /var/prog
COPY main.py ./

EXPOSE 514/udp

CMD [ "python", "main.py" ]