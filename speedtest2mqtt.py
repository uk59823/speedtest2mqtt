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
mqtt_topic = os.getenv('MQTT_TOPIC', 'main_uk/speedtest')
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
    count = 0
    while count < 5:
        try:
            # send MQTT message
            mqttclient = mqtt.Client(mqtt_clientid)
            mqttclient.on_connect = on_connectPublish
            if mqtt_user != "":
                mqttclient.username_pw_set(mqtt_user, mqtt_pass)
            mqttclient.connect(mqtt_ipaddress, mqtt_port, 60)
            mqttclient.loop_start()
            mqttpub = mqttclient.publish(
                topic, payload=message, qos=mqtt_qos, retain=mqtt_retain)
            mqttclient.loop_stop()
            mqttclient.disconnect()
            return True
        except:
            count += 1
            time.sleep(1)
    print("MQTT-Broker not reachable!")
    return False


def receive_mqtt_paho(topic):
    count = 0
    while count < 5:
        try:
            mqttSubscriber = mqtt.Client(mqtt_clientid)
            mqttSubscriber.on_connect = on_connectSubscribe
            if mqtt_user != "":
                mqttSubscriber.username_pw_set(mqtt_user, mqtt_pass)
            mqttSubscriber.connect(mqtt_ipaddress, mqtt_port, 60)
            mqttSubscriber.on_message = on_messageSubscribe
            mqttSubscriber.loop_forever()
            return True
        except:
            count += 1
            time.sleep(1)
    print("MQTT-Broker not reachable!")
    return False


def myspeedtest(count):
    res = {'download': 0, 'upload': 0, 'ping': 0}
    speedlist = []
    try:
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
        speedlist.insert(0, {'response': 'OK'})
        print(speedlist)
        return speedlist
    except:
        speedlist.insert(0, res)
        speedlist.insert(0, {'response': 'Error'})
        return speedlist


def main():

    dt = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    if send_mqtt_paho(dt, mqtt_topic + "/update") == False:
        return

    if connect() != True:
        print("[" + dt + "] - No internet connection")
        if send_mqtt_paho('408 Request Timeout (Internet connection)',
                          mqtt_topic + "/internet_response") == False:
            return
        if send_mqtt_paho(0, mqtt_topic + "/download") == False:
            return
        if send_mqtt_paho(0, mqtt_topic + "/upload") == False:
            return
        if send_mqtt_paho(0, mqtt_topic + "/ping") == False:
            return
        return "[" + dt + "] - 408 Request Timeout (Internet connection)"
    else:
        if send_mqtt_paho('200 OK', mqtt_topic + "/internet_response") == False:
            return

#    d, u, p = myspeedtest(count)
    speedlist = myspeedtest(count)

    if speedlist[0]['response'] == 'OK':
        d = speedlist[1]['download']
        u = speedlist[1]['upload']
        p = speedlist[1]['ping']

        if send_mqtt_paho('{:.2f}'.format(d/1048576), mqtt_topic + "/download") == False:
            return
        if send_mqtt_paho('{:.2f}'.format(u/1048576), mqtt_topic + "/upload") == False:
            return
        if send_mqtt_paho(p, mqtt_topic + "/ping") == False:
            return

        if send_mqtt_paho("OK", mqtt_topic + "/speedtest") == False:
            return

        return "[" + dt + "] - Download: {:.2f} Mbps; Upload: {:.2f} Mbps; Ping: {}".format(d/1048576, u/1048576, p)
    else:
        if send_mqtt_paho("Error", mqtt_topic + "/speedtest") == False:
            return
        return "[" + dt + "] - Error Speedtest"


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

            time.sleep(5)

        receive_mqtt_paho(mqtt_topic + "/start")
        time.sleep(10)
        b = message_received == "ON"
