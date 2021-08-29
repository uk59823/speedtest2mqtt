import speedtest
import urllib.request
import os
import time
import datetime
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe


# MQTT-Settings
mqtt_ipaddress = os.getenv('MQTT_BROKER', 'localhost')
mqtt_user = os.getenv('MQTT_USER', '')
mqtt_pass = os.getenv('MQTT_PASSWORD', '')
mqtt_topic = os.getenv('MQTT_TOPIC', 'main/speedtest')
mqtt_port = int(os.getenv('MQTT_PORT', '1883'))
mqtt_qos = int(os.getenv('MQTT_QOS', '2'))
mqtt_retain = eval(os.getenv('MQTT_RETAIN', 'True'))
mqtt_clientid = os.getenv('MQTT_CLIENTID', 'speed_mqtt')

count = int(os.getenv('TEST_COUNT', '1'))
interval = int(os.getenv('TEST_INTERVAL', '30'))

message_received = ""


def connect():
    host = 'http://google.com'
    try:
        urllib.request.urlopen(host)  # Python 3.x
        return True
    except:
        return False


def on_connectPublish(client, userdata, flags, rc):
    # Connect to MQTT-Broker
    if rc != 0:
        print("Connection Error to broker using Paho with result code " + str(rc))


def on_connectSubscribe(client, userdata, flags, rc):
    # Connect to MQTT-Broker
    client.subscribe(mqtt_topic + "/start")


def on_messageSubscribe(client, userdata, message):
    global message_received
    time.sleep(1)
    message_received = str(message.payload.decode("utf-8"))
    client.disconnect()


def send_mqtt_paho(message, topic):
    # send MQTT message
    mqttPublisher = mqtt.Client(mqtt_clientid)
    mqttPublisher.on_connect = on_connectPublish
    if mqtt_user != "":
        mqttPublisher.username_pw_set(mqtt_user, mqtt_pass)
    mqttPublisher.connect(mqtt_ipaddress, mqtt_port, 60)
    mqttPublisher.loop_start()
    mqttpub = mqttPublisher.publish(
        topic, payload=message, qos=mqtt_qos, retain=mqtt_retain)
    mqttPublisher.loop_stop()
    mqttPublisher.disconnect()


def receive_mqtt_paho(topic):
    mqttSubscriber = mqtt.Client(mqtt_clientid)
    mqttSubscriber.on_connect = on_connectSubscribe
    if mqtt_user != "":
        mqttSubscriber.username_pw_set(mqtt_user, mqtt_pass)
    mqttSubscriber.connect(mqtt_ipaddress, mqtt_port, 60)
    mqttSubscriber.on_message = on_messageSubscribe
    mqttSubscriber.loop_forever()


def myspeedtest(count):
    res = {'download': 0, 'upload': 0, 'ping': 0}
    speedlist = []
    s = speedtest.Speedtest()
    s.get_servers()
    s.get_best_server()
    for x in range(count):
        s.download()
        s.upload()
        resx = s.results.dict()
        speedlist.append(resx)
        res = {key: res[key] + resx.get(key, 0) for key in res.keys()}
    res = {key: res[key] // count for key in res.keys()}
    speedlist.insert(0, res)
    print("Average Values: " + res)
    print("Complete: " + speedlist)
    return speedlist


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

#    d, u, p = myspeedtest(count)
    speedlist = myspeedtest(count)
    d = speedlist[0]["download"]
    u = speedlist[0]["upload"]
    p = speedlist[0]["ping"]

    send_mqtt_paho('{:.2f}'.format(d/1048576), mqtt_topic + "/download")
    send_mqtt_paho('{:.2f}'.format(u/1048576), mqtt_topic + "/upload")
    send_mqtt_paho(p, mqtt_topic + "/ping")
    return "[" + dt + "] - Download: {:.2f} Mbps; Upload: {:.2f} Mbps; Ping: {}".format(d/1048576, u/1048576, p)


if __name__ == '__main__':
    print("speed2mqtt started")
    b = False
    send_mqtt_paho("OFF", mqtt_topic + "/start")
    dtNext = datetime.datetime.now()

    while 1:
        while (b or (datetime.datetime.now() >= dtNext)):
            dtStart = datetime.datetime.now()

            r = main()
            print(r)

            if b:
                b = False
                send_mqtt_paho("OFF", mqtt_topic + "/start")
            else:
                dtNext = dtStart + datetime.timedelta(seconds=interval*60)

        receive_mqtt_paho(mqtt_topic + "/start")
        b = message_received == "ON"
