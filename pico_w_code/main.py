from machine import Pin
import utime, time
import network
from umqtt.simple import MQTTClient
import urequests

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("Christian and Katie","thebears")
while not wlan.isconnected():
    time.sleep(1)
    print("connecting...")
print("connected")

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
while False: # example mqtt code
    client.publish(topic_pub, topic_msg)
    print("published...")
    client.subscribe(topic_pub)
    print("subbed...")
    time.sleep(3)

p0 = Pin(0, Pin.IN)

segments_pairs = [
    [Pin(n, Pin.IN) for n in pair]
    for pair in [(8, 9), (10, 11), (12, 13), (14, 15)]
]
esp_switch = Pin(17, Pin.OUT)
esp_switch.off()

esp_com = Pin(18, Pin.OUT)
esp_com.value(0)


led_pin = Pin(25, Pin.OUT)
def flicker():
    for i in range(4):
        led_pin.value(i%2)
        utime.sleep(0.25)

flicker()

waiting = True

# first and second input pins
set0 = {2, 3, 5}
set1 = {0, 1, 4, 6}

groups = [{6}, {4, 5}, {1, 3}, {0, 2}]

numbers = {
    (0, 1, 2, 4, 5, 6): 0,
    (2, 5): 1,
    (0, 2, 3, 4, 6): 2,
    (0, 2, 3, 5, 6): 3,
    (1, 2, 3, 5): 4,
    (0, 1, 3, 5, 6): 5,
    (0, 1, 3, 4, 5, 6): 6,
    (0, 1, 2, 5): 7,
    (0, 1, 2, 3, 4, 5, 6): 8,
    (0, 1, 2, 3, 5, 6): 9,
    (): "off",
}

def numbers_from_readings(readings):
    segments_on = set()
    for i, group in enumerate(groups):
        if readings[i][0]:
            segments_on |= group.intersection(set0)
        if readings[i][1]:
            segments_on |= group.intersection(set1)
    segments_on = tuple(sorted(list(segments_on)))
    if segments_on in numbers:
        return numbers[segments_on]
    else:
        print(f"Unknown readings : {readings}")
        return -1


def decode_numbers():
    """Called on a trigger read by pin 0"""
    values = []
    #utime.sleep(1/60/4/2)
    values.append([
        [not pin.value() for pin in pair]
        for pair in segments_pairs
    ])
    for i in range(3):
        utime.sleep(1/60/4)
        values.append([
            [not pin.value() for pin in pair]
            for pair in segments_pairs
        ])
    # change shape
    readings = [
        [values[i][k] for i in range(4)]
        for k in range(len(segments_pairs))
    ]
    #print(readings)
    nums = [
        numbers_from_readings(reading)
        for reading in readings[::-1]
    ]
    #print(nums)
    return nums

def write_to_mqtt(nums):
    ints = [
        0 if n == "off" else n
        for n in nums
    ]
    mass = 10*ints[0] + ints[1] + ints[2]/10 + ints[3]/100
    print(mass)
    urequests.get(f"https://script.google.com/macros/s/AKfycbw8iF5K5Iih_rjRmajQIaBLrIAoKE9XwQ7Y7KUP7VbScaOH7w43FG4PcAfmSCLmKkec/exec?mass={mass}", data=None, json=None, headers={})
    client.publish(topic_pub, f"{mass}")
    

fresh_reading = False
nums = ["off"]*4
while True:
    # wait for a trigger in, then read number
    while not p0.value():
        pass
    if p0.value():
        # we have a fresh signal and number
        #print("getting new numbers...")
        new_nums = decode_numbers()
        if (new_nums != ["off"]*4) and (-1 not in new_nums):
            nums = new_nums
            if nums != ["off", 0, 0, 0]:
                print(nums)
            fresh_reading = True # maybe redundant
    start_wait = time.ticks_ms()
    while (p0.value() and (time.ticks_ms() - start_wait < 50)):
        pass
    if time.ticks_ms() - start_wait >= 50:
        print("no more readings, writing maybe")
        # no more readings, write the last one and await the
        # next period of activity
        if fresh_reading:
            print("writing to mqtt")
            write_to_mqtt(nums)
            fresh_reading = False
        while p0.value():
            print("signal held high, waiting...")
            utime.sleep(1.12345)
