import os
import paho.mqtt.client as PahoMQTT
import json
import time
from MyMQTT import *
import requests

class PostValueThingspeak:

    def __init__(self, ClientID, broker,host,port):
        self.clientID=ClientID
        self.broker=broker
        self.host=host
        self.port=port
        self.initialize()
        self.client=MyMQTT(self.clientID,self.broker,1883,self)
        self.lastvalue = [0, 0, 0]

    def startOperation(self):
        self.client.start()
        time.sleep(3)
        self.subscribe()
           
    def notify(self,topic,payload):
        # all'arrivo del messaggio sul topic costruiamo l'URL per aggiungere il dato con richesta GET
        # esempio URL: https://api.thingspeak.com/update.json?api_key=ASGRXGIK2THFOBZC&field1=26
        url = "https://api.thingspeak.com/update?api_key="
        

        x = topic.split("/")
        print(x)
        
        # in base al secondo campo del topic sappiamo su quale canale publicare e quindi quale api_key utilizzare
        if x[1] == "1":
            url += str(self.key[0])
        elif x[1] == "2":
            url += str(self.key[1])
        elif x[1] == "3":
            url += str(self.key[2])
        elif x[1] == "4":
            url += str(self.key[3])
        else:
            print("Topic error. Aquarium code wrong")
        
        print(url)
        msg = json.loads(payload)
        value = str(msg["e"][0]["v"])
        print("messaggio")
        print(msg)
        print(value)

        # in base al quarto campo del topic sappiamo su quale field pubblicare
        if x[3] == "temperature":
            url += "&field1="+str(value)+"&field2="+str(self.lastvalue[1])+"&field3="+str(self.lastvalue[2])
            self.lastvalue[0] = value
        elif x[3] == "waterlevel":
            url += "&field1="+str(self.lastvalue[0])+"&field2="+str(value)+"&field3="+str(self.lastvalue[2])
            self.lastvalue[1] = value
        elif x[3] == "lightsensor":
            url += "&field1="+str(self.lastvalue[0])+"&field2="+str(self.lastvalue[1])+"&field3="+str(value)
            self.lastvalue[2] = value
        else:
            print("Topic error. Measurement typology wrong")

        # prendiamo dal payload il valore da pubblicare e lo inseriamo nell'URL
        
        print(url)

        # facciamo la richiesta GET
        response = requests.get(url)
        print(response)
    
    def initialize(self):
        catalog=requests.get("http://"+self.host+":"+str(self.port)+"/service").json()
        Thingspeak=catalog["thingspeak"]                                                         
        self.channel=[]
        self.topic={}
        self.key = []
        for i in Thingspeak.keys(): #i will be
            self.key.append(Thingspeak[i]["key"])
            self.channel.append(Thingspeak[i]["channel"])
            self.topic[i]=Thingspeak[i]["topic"]
            
    def subscribe(self):
        for i in self.topic.keys():
            self.client.mySubscribe(self.topic[i]+"/temperature")
            self.client.mySubscribe(self.topic[i]+"/waterlevel")
            self.client.mySubscribe(self.topic[i]+"/lightsensor")
  
if __name__=="__main__":    
    host = os.environ['CATALOG_HOST']
    port=os.environ['CATALOG_PORT']

    # lista di api_key che associ il numero dell'acquario (1,2,3,4) al corrispettivo api_key
    #api_key = ["ASGRXGIK2THFOBZC","ASGRXGIK2THFOBZC","ASGRXGIK2THFOBZC","ASGRXGIK2THFOBZC"]

    # lista di topic ai quali fare il Sub
    #topicSub = ["IoT/1/sensors/temperature","IoT/1/sensors/waterlevel","IoT/1/sensors/light","IoT/1/sensors/feed","IoT/2/sensors/temperature","IoT/2/sensors/waterlevel","IoT/2/sensors/ligh","IoT/2/sensors/feed","IoT/3/sensors/temperature","IoT/3/sensors/waterlevel","IoT/3/sensors/ligh","IoT/3/sensors/feed","IoT/4/sensors/temperature","IoT/4/sensors/waterlevel","IoT/4/sensors/ligh","IoT/4/sensors/feed"]

    AdaptorPublisher = PostValueThingspeak("ThingSpeak1234","mqtt.eclipseprojects.io", host, port)
    AdaptorPublisher.startOperation()

    while True:
        time.sleep(0.1)