from machine import Pin
import utime

p0 = Pin(0, Pin.IN)

segments_pairs = [
    [Pin(n, Pin.IN) for n in pair]
    for pair in [(8, 9), (10, 11), (12, 13), (14, 15)]
]
output = Pin(17, Pin.OUT)

waiting = True

def numbers_from_readings(readings):
    if readings == [[0, 0], [0, 0], [0, 0], [0, 0]]:
        return "off"
    elif readings in [
        [[1, 1], [1, 1], [0, 1], [1, 1]], # least sig
        [[0, 1], [1, 1], [0, 1], [1, 1]], # second least sig (with .)
    ]:
        return 0
    elif readings in [
        [[True, False], [True, False], [False, False], [True, False]],
        [[False, False], [True, False], [False, False], [True, False]],
    ]:
        return 1
    elif readings in [
        [[1, 1], [0, 1], [1, 0], [1, 1]],
        [[False, True], [False, True], [True, False], [True, True]],
    ]:
        return 2
    elif readings in [
        [[True, True], [True, False], [True, True], [False, True]],
        [[False, True], [True, False], [True, True], [False, True]],
    ]:
        return 6
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
    print(readings)
    print([
        numbers_from_readings(reading)
        for reading in readings[::-1]
    ])
    # signal that we're done
    output.on()
    utime.sleep(1/1000)
    output.off()
    utime.sleep(1)

while True:
    if p0.value() and waiting:
        output.on()
        utime.sleep(1/1000)
        output.off()
        waiting = False
        ## when triggering off P2, looks like you wait this long...
        #utime.sleep(3/(60*4))
        decode_numbers()
    elif not p0.value():
        if not waiting:
            waiting = True
