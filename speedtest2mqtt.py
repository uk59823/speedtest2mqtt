import speedtest
import urllib.request
import os
import time
import datetime
import paho.mqtt.client as mqtt				        # using MQTT-client


# MQTT-Settings
mqtt_ipaddress = os.getenv('MQTT_BROKER', 'localhost')
mqtt_user = os.getenv('MQTT_USER', '')
mqtt_pass = os.getenv('MQTT_PASSWORD', '')
mqtt_topic = os.getenv('MQTT_TOPIC', 'master/speedtest')
mqtt_port = int(os.getenv('MQTT_PORT', '1883'))
mqtt_qos = int(os.getenv('MQTT_QOS', '2'))
mqtt_retain = eval(os.getenv('MQTT_RETAIN', 'True'))
mqtt_clientid = os.getenv('MQTT_CLIENTID', 'speed_mqtt')
interval = int(os.getenv('TEST_INTERVAL', '30'))


def connect():
    host = 'http://google.com'
    try:
        urllib.request.urlopen(host)  # Python 3.x
        return True
    except:
        return False


def on_connect(client, userdata, flags, rc):
    # Connect to MQTT-Broker
    if rc != 0:
        print("Connection Error to broker using Paho with result code " + str(rc))


def send_mqtt_paho(message, topic):
    # send MQTT message
    mqttclient = mqtt.Client(mqtt_clientid)
    mqttclient.on_connect = on_connect
    if mqtt_user != "":
        mqttclient.username_pw_set(mqtt_user, mqtt_pass)
    mqttclient.connect(mqtt_ipaddress, mqtt_port, 60)
    mqttclient.loop_start()
    mqttpub = mqttclient.publish(
        topic, payload=message, qos=mqtt_qos, retain=mqtt_retain)
    mqttclient.loop_stop()
    mqttclient.disconnect()


def myspeedtest():
    s = speedtest.Speedtest()
    s.get_servers()
    s.get_best_server()
    s.download()
    s.upload()
    res = s.results.dict()
    return res["download"], res["upload"], res["ping"]


def main():

    dt = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    send_mqtt_paho(dt, mqtt_topic + "/update")

    if connect() != True:
        print("[" + dt + "] - No internet connection")
        send_mqtt_paho('408 Request Timeout (Internet connection)',
                       mqtt_topic + "/internet_response")
        send_mqtt_paho(0, mqtt_topic + "/download")
        send_mqtt_paho(0, mqtt_topic + "/upload")
        send_mqtt_paho(0, mqtt_topic + "/ping")
        return "[" + dt + "] - 408 Request Timeout (Internet connection)"
    else:
        send_mqtt_paho('200 OK', mqtt_topic + "/internet_response")

    d, u, p = myspeedtest()

    send_mqtt_paho('{:.2f}'.format(d/1048576), mqtt_topic + "/download")
    send_mqtt_paho('{:.2f}'.format(u/1048576), mqtt_topic + "/upload")
    send_mqtt_paho(p, mqtt_topic + "/ping")
    return "[" + dt + "] - Download: {:.2f} Mbps; Upload: {:.2f} Mbps; Ping: {}".format(d/1048576, u/1048576, p)


if __name__ == '__main__':
    print("speed2mqtt started")

    while 1:
        dtStart = datetime.datetime.now()
        r = main()
        print(r)
        dtEnd = datetime.datetime.now()
        time.sleep(interval*60 - (dtEnd - dtStart).total_seconds())
