import RPi.GPIO as GPIO
import time
import paho.mqtt.client as PahoMQTT
import json
import time
import requests
from MyMQTT import *
class Light:
    def __init__(self,ClientID,broker,topic,pin):
        self.clientID=ClientID
        self.broker=broker    
        self.pin=pin  
        self.client=MyMQTT(self.clientID,self.broker,1883,self)
        self.topic=topic
    
    def startOperation(self):
        self.client.start()
        self.client.mySubscribe(self.topic)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
    
    def notify(self,topics,payload):
        msg=json.loads(payload)
        print(msg["e"][0]["l"])

        if msg["e"][0]["l"]==0:
            GPIO.output(self.pin, GPIO.LOW)
        else:
            GPIO.output(self.pin, GPIO.HIGH)

if __name__=="__main__":
    lightbulb=Light("Alex99sff979777654","mqtt.eclipseprojects.io","IoT/1/control/light",7)
    lightbulb.startOperation()
    while True:
        time.sleep(10)































