import time

import paho.mqtt.client as mqtt #import the client1
broker_address="localhost" 
client = mqtt.Client("P1") #create new instance
client.connect(broker_address) #connect to broker
topic = "van/solar/power"


from solarshed.controllers.renogy_rover import RenogyRover
controller = RenogyRover('/dev/ttyUSB0', 1)

SCRAPE_DELAY = 1


while True:
    payload = '{"power":' + str(controller.solar_power()) + '}'
    client.publish(topic,payload)
    time.sleep(SCRAPE_DELAY)

