import paho.mqtt.client as PahoMQTT
import json
import time
from MyMQTT import *
class heater:
    def __init__(self,ClientID,broker,topic):
        self.clientID=ClientID
        self.broker=broker

        self.client=MyMQTT(self.clientID,self.broker,1883,self)
        self.topic=topic
    
    def startOperation(self):
        self.client.start()
        self.client.mySubscribe(self.topic)
    def notify(self,topics,payload):
        print("cuao")
        msg=json.loads(payload)
        print(msg)


if __name__=="__main__":
    heater=heater("Alex99ddffhgcf","mqtt.eclipseprojects.io","IoT/1/sensors/heater")
    heater.startOperation()
    while(1):
        time.sleep(1)
