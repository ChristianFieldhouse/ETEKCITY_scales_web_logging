from machine import Pin, PWM, Timer
import utime, time

clk = Pin(1, Pin.OUT)
cs = Pin(2, Pin.OUT)

voltage_set = PWM(Pin(15))
voltage_set.freq(1000)
voltage_set.duty_u16(0)

current_set = PWM(Pin(14))
current_set.freq(1000)
current_set.duty_u16(0)

current_get = analog_value = machine.ADC(26)

class RotaryEncoder():
    def __init__(self, value, step, pin_a, pin_b, on_update):
        self.a = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self.b = Pin(pin_b, Pin.IN, Pin.PULL_UP)
        self.a.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=lambda x: self.a_change())
        self.b.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=lambda x: self.b_change())
        #self.a.irq(trigger=, handler=lambda x: self.check_done())
        #self.b.irq(trigger=Pin.IRQ_RISING, handler=lambda x: self.check_done())
        self.transitioning = False
        self.transition_start = 0
        self.value = value
        self.step = step
        self.on_update = on_update
    def a_change(self):
        if self.a.value():
            self.check_done()
        else:
            self.a_down()
    def b_change(self):
        if self.b.value():
            self.check_done()
        else:
            self.b_down()
    def a_down(self):
        #print("a down")
        if not self.transitioning:
            self.transitioning = "from a"
            self.transition_start = time.ticks_us()
        elif self.transitioning == "from b": # b already down
            self.value += self.step
            self.transitioning = "ab"
            print(self.value)
            self.on_update()
    def b_down(self):
        #print("b down")
        if not self.transitioning:
            self.transitioning = "from b"
            self.transition_start = time.ticks_us()
        elif self.transitioning == "from a": # a already down
            self.value -= self.step
            if self.value < 0:
                self.value = 0
            self.transitioning = "ba"
            print(self.value)
            self.on_update()
    def check_done(self):
        """check if we're done transitioning"""
        if (
            (self.a.value() and self.b.value()) and
            time.ticks_us() - self.transition_start > 100
        ):
            self.transitioning = False

def update_va():
    set_va(mv.value/1000, ma.value/1000)

mv = RotaryEncoder(3300, 100, 16, 17, on_update=update_va)
ma = RotaryEncoder(100, 10, 19, 18, on_update=update_va)

def set_voltage(v):
    """Appears to be linear 0-30v"""
    voltage_set.duty_u16(int((2**16-1)*max(v, 0)/30))

def set_current(a):
    """Very approximate"""
    current_set.duty_u16(int((2**16-1)*max(a, 0)/5))

def get_current():
    return 5 * (2.5/3.3) *current_get.read_u16()/(2**16 - 1)

def set_va(v, a):
    text = format_voltage(v) + format_current(a) + format_voltage(v*a)
    print(text)
    update_display(text, dots=(1, 4, 9))
    #set_voltage(v)
    #set_current(a)

cs.on() # go low for instruction

# start from lowest bits
data = [0, 1, 0, 0, 0, 0, 0, 0][::-1] + [1,]*16

segments = {
    "0": (0, 1, 2, 3, 5, 7),
    "1": (3, 5),
    "2": (1, 3, 4, 0, 7),
    "3": (1, 3, 4, 5, 7),
    "4": (2, 3, 4, 5),
    "5": (1, 2, 4, 5, 7),
    "6": (0, 1, 2, 4, 5, 7),
    "7": (1, 2, 3, 5),
    "8": (0, 1, 2, 3, 4, 5, 7),
    "9": (1, 2, 3, 4, 5, 7),
    "*": (0, 1, 2, 3, 4, 5, 6, 7),
    "C": (0, 1, 2, 7),
    "h": (0, 2, 4, 5),
    "r": (0, 4),
    "i": (0,),
    "s": (1, 2, 4, 5, 7),
    "t": (0, 2, 4, 7),
    "a": (0, 4, 5, 6, 7),
    "n": (0, 4, 5),
    "e": (0, 1, 2, 3, 4, 7),
    ".": (6,),
    " ": (),
}

def read_keyscan(tick = 0.0001):
    read_command = [0, 1, 0, 0, 0, 0, 1, 0]
    cs.off()
    clk.off()
    utime.sleep(tick)
    dio = Pin(3, Pin.OUT)
    for d in read_command:
        #print(d)
        clk.off()
        utime.sleep(tick)
        dio.value(d)
        utime.sleep(tick)
        clk.on()
        utime.sleep(tick)
    utime.sleep(0.001) # "at least 1us"
    dio = Pin(3, Pin.IN)
    vals = []
    for i in range(8):
        for k in range(4):
            clk.off()
            utime.sleep(tick)
            if k == 3:
                vals.append(dio.value())
            utime.sleep(tick)
            clk.on()
            utime.sleep(tick)
    clk.off()
    cs.on()
    return vals

def write_serial(data, tick = 0.0001):
    cs.off()
    clk.off()
    utime.sleep(tick)
    dio = Pin(3, Pin.OUT)
    for d in data:
        #print(d)
        clk.off()
        utime.sleep(tick)
        dio.value(d)
        utime.sleep(tick)
        clk.on()
        utime.sleep(tick)
    clk.off()
    cs.on()

def turn_display_on():
    # works!!!
    data = [1, 0, 0, 0, 1, 0, 0, 0][::-1]
    write_serial(data)

def set_address(addr=0):
    data = ([1, 1, 0, 0] + [c=="1" for c in '{0:04b}'.format(addr)])[::-1]
    write_serial(data)

def update_memory(n, addr=0):
    set_address(addr)
    data = [0, 1, 0, 0, 0, 0, 0, 0][::-1]
    nbits = [c=="1" for c in '{0:016b}'.format(n)]
    bit_data = nbits[:8][::-1] + nbits[8:16][::-1]
    write_serial(data+bit_data)

def update_display(digits=None, dots=()):
    new_memory = [0 for _ in range(8)] #2-byte words
    remap = [4, 5, 6, 7, 13, 12, 11, 14, 1, 0, 15, 2] #3 is the colour leds
    for i, d in enumerate(digits):
        for segment in range(8):
            if segment in segments[d]:
                new_memory[segment] += 2**(15-remap[i])
    # add dots
    for dot in dots:
        new_memory[6] += 2**(15-remap[dot])
    for addr, word in zip(range(0, 16, 2), new_memory):
        update_memory(word, addr)

turn_display_on()
update_display(" Christian")

def format_voltage(v):
    if v > 1:
        return f"{round(v*100): 4d}"
    return " " + f"{round(v*100):03d}"

def format_current(a):
    return f"{round(a*1000):04d}"

class KeyscanButtons():
    def __init__(self):
        self.output = False
        self.voltage = False
        self.current = False
        self.output_change = time.ticks_ms()
        self.voltage_change = time.ticks_ms()
        self.current_change = time.ticks_ms()

    def keyscan_update(self):
        k = read_keyscan()
        t = time.ticks_ms()
        too_soon = 1000
        if k[0] and (t - self.output_change) > too_soon:
            self.output = not self.output
        if k[1] and (t - self.voltage_change) > too_soon:
            self.voltage = not self.voltage
        if k[2] and (t - self.current_change) > too_soon:
            self.current = not self.current
        print(self.output, self.voltage, self.current)

keyscan_buttons = KeyscanButtons()
tim = Timer(period=100, mode=Timer.PERIODIC, callback=lambda t: keyscan_buttons.keyscan_update())

