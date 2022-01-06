FROM python:3

ENV MQTT_BROKER=0.0.0.0 \
    MQTT_PORT=1883\
    MQTT_CLIENTID=syslog_to_mqtt\
    MQTT_USERNAME=username\
    MQTT_PASSWORD=password\
    MQTT_PREFIX=syslog\
    PYTHONUNBUFFERED=1

RUN pip3 install paho-mqtt
RUN pip3 install syslogmp

WORKDIR /var/prog
COPY main.py ./

EXPOSE 514/udp

CMD [ "python", "main.py" ]