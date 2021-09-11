import time

#Import the MQTT client and connect to the MQTT broker at localhost
import paho.mqtt.client as mqtt #import the client
broker_address="localhost" #Change this line if the MQTT broker is running somewhere else
client = mqtt.Client("P1") #create new instance
client.connect(broker_address) #connect to broker

#Set the MQTT topic to publish data to
topic = "van/solar/power"

#Import the Renogy Rover charge controller library and connect to the serial USB dongle
from solarshed.controllers.renogy_rover import RenogyRover
controller = RenogyRover('/dev/ttyUSB0', 1) #Change this line if the USB dongle has a different address

#Set the time between data captures in seconds
SCRAPE_DELAY = 1


while True:
    payload = '{"power":' + str(controller.solar_power()) + '}' #Read the current solar power
    client.publish(topic,payload)
    time.sleep(SCRAPE_DELAY)

