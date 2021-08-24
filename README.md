# speedtest2mqtt
Check the internet speed via **speedtest cli** and send the result to MQTT

# The functionality of the script
The script first check the internet availibility and then the internet speed at intervals (download, upload, ping, time stamp) and sends the values to an MQTT broker. It should never stop ;-) only when an error occurs.

# Environment
The script is intended for use in a Docker container, so that the Docker environment variables are used to control the script
https://hub.docker.com/repository/docker/ukrae/speedtest2mqtt

## docker environment variables
### MQTT-Settings 
* MQTT_BROKER: IP-Address (or FQN) of your MQTT Broker (*default: 'localhost'*)
* MQTT_PORT: Port for your Broker (*default: 1883*)
* MQTT_QOS: QOS-level for the message (*default: 2*)
* MQTT_RETAIN: True/False for telling the MQTT-server to retain the message or discard it (*default: True*)
* MQTT_TOPIC: MQTT topic for the JSON (*default: 'master/speedtest'*)
* MQTT_USER: Username for the broker (*leave empty for anonymous call*)
* MQTT_PASSWORD: Password for the broker (*leave empty for anonymous call*)
* MQTT_CLIENTID: ClientID for the broker to avoid parallel connections (*default: 'speed_mqtt'*)

### other Settings
* TEST_INTERVAL: Interval (in minutes) in which the speedtest is checked (*default: 30*)

## Output
* master/speedtest/download
* master/speedtest/upload
* master/speedtest/ping
* master/speedtest/update
* master/speedtest/internet_response
