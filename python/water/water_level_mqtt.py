import time
from datetime import datetime

import board
import busio
i2c = busio.I2C(board.SCL, board.SDA)

import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

ads = ADS.ADS1115(i2c)
chan = AnalogIn(ads, ADS.P0)


#import adafruit_ads1x15
#adc = adafruit_ads1x15.ads1115()

import paho.mqtt.client as mqtt #import the client1
broker_address="localhost" 
client = mqtt.Client("P2") #create new instance
client.connect(broker_address) #connect to broker
topic = "van/adc/water"

SCRAPE_DELAY = 1


while True:

    #Voltage range is from about 1.14V to 2.48V
    #When empty the voltage should go to 0V
    #water_volts = adc.read_adc(0, 1)
    #water_volts = (water_volts/32767.)*4.048

    water_volts = chan.voltage

    if water_volts > 2.2:
        water_pct = 100
    elif water_volts > 2:
        water_pct = 93
    elif water_volts > 1.9:
        water_pct = 87
    elif water_volts > 1.8:
        water_pct = 80
    elif water_volts > 1.75:
        water_pct = 73
    elif water_volts > 1.675:
        water_pct = 67
    elif water_volts > 1.625:
        water_pct = 60
    elif water_volts > 1.575:
        water_pct = 53
    elif water_volts > 1.5:
        water_pct = 47
    elif water_volts > 1.45:
        water_pct = 40
    elif water_volts > 1.4:
        water_pct = 33
    elif water_volts > 1.3:
        water_pct = 27
    elif water_volts > 1.2:
        water_pct = 20
    elif water_volts > 1.1:
        water_pct = 13
    elif water_volts > 1:
        water_pct = 7
    else:
        water_pct = 0

    payload = '{"percent":' + str(water_pct) + ',"volts":' + str(water_volts) + '}'
    client.publish(topic,payload)

#    f=open("/home/pi/water/water_log.txt", "a+")
#    f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + str(water_volts) + " " + str(water_pct) + "\n")
#    f.close()

    time.sleep(SCRAPE_DELAY)


