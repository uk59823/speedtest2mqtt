FROM python:3.8-alpine

ENV TZ=Europe/Berlin
ENV MQTT_BROKER=localhost
ENV MQTT_PORT=1883
ENV MQTT_QOS=2
ENV MQTT_RETAIN=True
ENV MQTT_TOPIC=master/speedtest
ENV MQTT_USER= 
ENV MQTT_PASSWORD= 
ENV MQTT_CLIENTID=speed_mqtt
ENV TEST_INTERVAL=30

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
	
ADD speedtest2mqtt.py /

CMD [ "python", "./speedtest2mqtt.py" ]