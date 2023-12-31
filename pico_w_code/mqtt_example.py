import network
import time
from machine import Pin
from umqtt.simple import MQTTClient

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("Christian and Katie","thebears")
while not wlan.isconnected():
    time.sleep(1)
    print("connecting...")
print("connected")

sensor = Pin(16, Pin.IN)

mqtt_server = '192.168.1.108'
client_id = 'scales'
topic_pub = b'PersonWeight'
topic_msg = b'error-no-weight-detected'
mqtt_user = 'scales'
mqtt_password = 'scales_password'


def sub_cb(topic, msg):
    print("New message on topic {}".format(topic.decode('utf-8')))
    msg = msg.decode('utf-8')
    print(msg)

def mqtt_connect():
    client = MQTTClient(
        client_id,
        mqtt_server,
        keepalive=3600,
        user=mqtt_user,
        password=mqtt_password,
    )
    client.set_callback(sub_cb)
    client.connect()
    print('Connected to %s MQTT Broker'%(mqtt_server))
    return client

def reconnect():
    print('Failed to connect to the MQTT Broker. Reconnecting...')
    time.sleep(5)
    machine.reset()

client = mqtt_connect()

#try:
#    
#except OSError as e:
#    reconnect()
while True:
    client.publish(topic_pub, topic_msg)
    print("published...")
    client.subscribe(topic_pub)
    print("subbed...")
    time.sleep(3)
    if sensor.value() == 0:
        client.publish(topic_pub, topic_msg)
        time.sleep(3)
    else:
        pass