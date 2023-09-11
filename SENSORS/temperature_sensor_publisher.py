import paho.mqtt.client as PahoMQTT
import json
import time
import glob
import Adafruit_DHT

from MyMQTT import *
class Temperaturesensor:
    def __init__(self,ClientID,broker,topic):
        self.clientID=ClientID
        self.broker=broker
        self.topic=topic
        self.client=MyMQTT(self.clientID,self.broker,1883,None) #notifier not necessary
        self.DHT11 = Adafruit_DHT.DHT11                                   
        self.DHT11_PIN = 17

        
    def startOperation(self):
        self.client.start()
        time.sleep(3)
        
        
        
    def publishTemperaturestatus(self):
        self.umidita, self.temperatura = Adafruit_DHT.read_retry(self.DHT11, self.DHT11_PIN)
        
        msg={"bn": "alex/sensor1/temperature","e":[{"n":"temperature","u": "Cel","t":time.time(),"v":self.temperatura}]};
        #msg={"bn": "IoT/sensor/temperature","e":[{"n":"DFR0198","u": "Cel","t":time.time(),"v":value}]};
        self.client.myPublish(self.topic,msg)
        print(msg)


      

if __name__=="__main__":
    temp=Temperaturesensor("Alex99966834rr","mqtt.eclipseprojects.io","IoT/1/sensors/temperature")
    
    temp.startOperation()
    
    while 1:
        
        temp.publishTemperaturestatus()
        time.sleep(3)










