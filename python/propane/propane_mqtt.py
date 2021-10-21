import sys
import os
import struct
import subprocess
from ctypes import (CDLL, get_errno)
from ctypes.util import find_library
from socket import (
    socket,
    AF_BLUETOOTH,
    SOCK_RAW,
    BTPROTO_HCI,
    SOL_HCI,
    HCI_FILTER,
)

### Set up MQTT connection
import paho.mqtt.client as mqtt #import the client1
broker_address="localhost" 
client = mqtt.Client("P3") #create new instance
client.connect(broker_address) #connect to broker
topic = "van/propane"

### Bluetooth address for the sensor
ble_address = "90:9a:77:1e:8f:db"

### Set up bluetooth
if not os.geteuid() == 0:
    sys.exit("script only works as root")

btlib = find_library("bluetooth")
if not btlib:
    raise Exception(
        "Can't find required bluetooth libraries"
        " (need to install bluez)"
    )
bluez = CDLL(btlib, use_errno=True)

dev_id = bluez.hci_get_route(None)

sock = socket(AF_BLUETOOTH, SOCK_RAW, BTPROTO_HCI)
sock.bind((dev_id,))

err = bluez.hci_le_set_scan_parameters(sock.fileno(), 0, 0x10, 0x10, 0, 0, 1000);
if err < 0:
    raise Exception("Set scan parameters failed")
    # occurs when scanning is still enabled from previous call

# allows LE advertising events
hci_filter = struct.pack(
    "<IQH", 
    0x00000010, 
    0x4000000000000000, 
    0
)
sock.setsockopt(SOL_HCI, HCI_FILTER, hci_filter)

err = bluez.hci_le_set_scan_enable(
    sock.fileno(),
    1,  # 1 - turn on;  0 - turn off
    0, # 0-filtering disabled, 1-filter out duplicates
    1000  # timeout
)
if err < 0:
    errnum = get_errno()
    raise Exception("{} {}".format(
        errnum.errorcode[errnum],
        os.strerror(errnum)
    ))


### This function is essentially the same as the "GetPulseEchoTime2"
### function from the tank check app. I honestly have no idea what
### it's doing with the data, but I converted it as well as I could
### from javascript to python and compared the results of a few readings
### to the app and the results lined up, so I didn't mess with it any more
def GetPulseEchoTime(adv):
    def a(a, b):
        c = .5 * 1.2421875
        e = (255 - b) / 256
        if c >= a:
            return 0
        else:
            return (a-c)*e

    e = len(adv)
    c = adv
    k = [0]
    b = 1
    while (b < e):
        g = c[b - 1][1] / 2
        h = c[b][1] / 2
        if (h - 1) != g:
            k.append(b)
        b += 1
    g = []
    l = []
    h = len(k)
    p = 0
    b = 0
    while (b < h):
        n = m = 0
        if b == h - 1:
            q = e
        else:
            q = k[b+1]
        f = p
        while (f < q):
            if c[f][0] > m:
                n = f
                m = c[f][0]
            f += 1
        g.append(n)
        f = p
        while (f < q):
            l.append(m)
            f += 1
        p = q
        b += 1
    n = []
    m = []
    b = 0
    while (100 > b):
        n.append(0)
        m.append(0)
        b += 1
    k = len(n)
    b = 0
    while (b < e):
        l = c[b][1] // 2
        p = c[b][0]
        p = a(p, l)
        n[l] += .5 * p
        f = b + 1
        while (f < e):
            q = c[f][1] // 2
            t = q - l
            r = c[f][0]
            r = a(r, q)
            if p < r:
                r = p
            n[t] += r
            f += 1
        b += 1
    b = 0
    while (b < h):
        l = c[g[b]][1] // 2
        p = c[g[b]][1]
        m[l] += a(p, l)
        f = b + 1
        while (f < h):
            q = c[g[f]][1] // 2
            t = q - l
            r = c[g[f]][0]
            r = (a(r, q) + a(p, l)) / 2
            m[t] += r
            f += 1
        b += 1
    score_filt = []
    score_filt.append(.25 * n[1] + .5 * n[0])
    score_filt[0] += .5 * m[1] + .5 * m[0]
    b = 1
    while (b < k - 1):
        score_filt.append(.25 * (n[b - 1] + n[b + 1]) + .5 * n[b])
        score_filt[b] += .5 * (m[b - 1] + m[b + 1]) + .5 * m[b]
        b += 1
    score_filt.append(.25 * n[k - 2] + .5 * n[k - 1])
    score_filt[k - 1] += .5 * m[k - 2] + .5 * m[k - 1]
    n = 0
    m = .005
    b = 2
    while (b < k):
        if score_filt[b] > m:
            m = score_filt[b]
            n = b
        b += 1
    b = g = 0
    while (b < e):
        if (c[b][0] > g):
            g = c[b][0]
        b += 1
    if (.63453125 >= g):
        return 0
    calculated_level = 2E-5 * n
    return calculated_level


### "convertLevelToInches" function from the app
### translated from javascript to python
### Again, I'm not really sure what it's doing
### but it works
def convertLevelToInches(level, temperature, hwVersionNumber):
    r = temperature
    a = r * r
    if (65 == hwVersionNumber):
        n = 93009E-9 * r * a - .04122379 * a + 4.579691847 * r + 1404.337855187
    else:
        if (r <= -39):
            if (level <= 0):
                return 0
            t = 1E3 * level * 1E3 * 0.015 + 0.5
            return t
        n = 1040.71 - 4.87 * r - 137.5 - .0107 * r * r - 1.63 * r
    if level <= 0:
        return 0
    i = level * n / 2 * 39.3701
    return i


### "getPercentFromHeight" function from the app
### translated from javascript to python
def getPercentFromHeight(e):
    height = 0.254 #constant found in the app
    tank_min_offset = 0.0381 #constant found in the app

    n = height
    t = 100 * (e - tank_min_offset) / (n - tank_min_offset)
    if t < 0:
        return 0
    if t > 100:
        return 100

    return round(t)


### This function takes the raw advertisement data from the BLE sensor
### and processes it into readable data. The functions were taken from
### decompiling V2.5.1 of the Mopeka Tank Check App using apktool
### Functions were found in the dist.bundle.js javascript file
def parse_data(x):
    e = x[16:41] #Select the relevant data from the BLE advertisement
    e = list(map(lambda i: int(i, 16), e)) #Convert data from hex to int

    ### The following code comes from the "class LA extends SA" constructor
    if 1 == (1 & e[3]):
        hwFamily = "xl"
    else:
        hwFamily = "gen2"

    hwVersionNumber = 207 & e[3]
    qualityStars = e[3] >> 4 & 3
    battery = e[4] / 256 * 2 + 1.5

    ### The battery percent calculation comes fomr the "getBatteryPercentage()" function
    battery_pct = (battery - 2.2) / .65 * 100
    if battery_pct < 0:
        battery_pct = 0
    elif battery_pct > 100:
        battery_pct = 100
    else:
        battery_pct = round(battery_pct)

    ### Back to the "class LA extends SA" constructor
    r = 63 & e[5]

    if r == 0:
        temperature = -40
    else:
        temperature = 1.776964 * (r - 25)

    slowUpdateRate = not not (64 & e[5])
    syncPressed = not not (128 & e[5])

    ### The "else" statement at the end of the constructor
    ### which the app seems to always enter
    t = 0
    n = 0
    r = 6
    adv = []
    for a in range(12):
        i = 10 * a
        o = i // 8
        c = i % 8
        s = e[r + o] + 256 * e[r + o + 1]
        s >>= c
        l = 1 + (31 & s)
        s >>= 5
        u = 31 & s
        A = n + l
        n = A
        if A > 255:
            break
        if u != 0:
            u -= 1
            u *= 4
            u += 6
            adv.append((u, 2*A)) #u is a, 2*A is index
            t += 1


    ### That is the end of the constructor. The semi-processed data
    ### is snow stored in the "adv" list. The next modification to
    ### the data was in a function called "GetPulseEchoTime2"
    ### which returns a calculated level variable
    level = GetPulseEchoTime(adv)

    ### The next function takes the level value calculated above and
    ### converts it to inches of propane. This function was taken from
    ### the "convertLevelToInches" function in the app
    inches = convertLevelToInches(level, temperature, hwVersionNumber)

    ### The next function takes the level in meters as input
    ### so we first convert it from inches to meters
    meters = inches / 39.3701

    ### The final function converts the level in meters to a percentage
    percent = getPercentFromHeight(meters)

    return percent, qualityStars, battery_pct, temperature


while True:
    data = sock.recv(1024)
    # Check if the bluetooth address matches, then decode and send data
    if ':'.join("{0:02x}".format(x) for x in data[12:6:-1]) == ble_address:
        x = ' '.join("{0:02x}".format(x) for x in data).split(' ')
        propane_pct, propane_qual, propane_bat, propane_temp = parse_data(x)
        payload = '{"propane_pct":' + str(propane_pct) + ',"propane_qual":' + str(propane_qual) + ',"propane_bat":' + str(propane_bat) + ',"propane_temp":' + str(propane_temp) + '}'
        client.publish(topic,payload)

