import os
import paho.mqtt.client as PahoMQTT
import json
import time
from MyMQTT import *
import requests

class PostValueThingspeak:
    def __init__(self, ClientID, broker, host, port):
        self.clientID = ClientID
        self.broker = broker
        self.host = host
        self.port = port
        self.initialize()
        self.client = MyMQTT(self.clientID, self.broker, 1883, self)
        self.lastvalue = [0, 0, 0]

    def startOperation(self):
        self.client.start()
        time.sleep(3)
        self.subscribe()
           
    def notify(self, topic, payload):
        # When a message arrives on the topic, the URL is composed to reach de data with a get request
        # Example URL: https://api.thingspeak.com/update.json?api_key=ASGRXGIK2THFOBZC&field1=26
        url = "https://api.thingspeak.com/update?api_key="
        
        x = topic.split("/")
        
        # The second field of the topic is the channel on which publish, so which api_key to use
        if x[1] == "1":
            url += str(self.key[0])
        elif x[1] == "2":
            url += str(self.key[1])
        elif x[1] == "3":
            url += str(self.key[2])
        elif x[1] == "4":
            url += str(self.key[3])
        else:
            print("ADAPTOR Topic error. Aquarium code is wrong!")
        
        msg = json.loads(payload)
        print(f"ADAPTOR Notifying on topic {topic} with msg {msg}")

        if x[3] == "light":
            value = str(msg["e"][0]["l"])  
        else:
            value = str(msg["e"][0]["v"])
        
        # The fourth field of the topic is the field on which to publish, also the value for each field is added to the URL
        if x[3] == "temperature":
            url += "&field1="+str(value)+"&field2="+str(self.lastvalue[1])+"&field3="+str(self.lastvalue[2])
            self.lastvalue[0] = value
        elif x[3] == "waterlevel":
            url += "&field1="+str(self.lastvalue[0])+"&field2="+str(value)+"&field3="+str(self.lastvalue[2])
            self.lastvalue[1] = value
        elif x[3] == "light":
            url += "&field1="+str(self.lastvalue[0])+"&field2="+str(self.lastvalue[1])+"&field3="+str(value)
            self.lastvalue[2] = value
        else:
            print("ADAPTOR Topic error. Measurement type is wrong!")
        
        print(f"ADAPTOR The complete URL is {url}")

        # GET request
        response = requests.get(url)
        print(f"ADAPTOR GET request ended with status: {response}")
    
    def initialize(self):
        catalog = requests.get("http://"+self.host+":"+str(self.port)+"/service").json()
        Thingspeak = catalog["thingspeak"]                                                         
        self.channel = []
        self.topic = {}
        self.key = []

        for i in Thingspeak.keys():
            self.key.append(Thingspeak[i]["key"])
            self.channel.append(Thingspeak[i]["channel"])
            self.topic[i]=Thingspeak[i]["topic"]
            
    def subscribe(self):
        for i in self.topic.keys():
            acquariumcode = self.topic[i].split("/")[1]
            self.client.mySubscribe(self.topic[i]+"/temperature")
            self.client.mySubscribe(self.topic[i]+"/waterlevel")
            self.client.mySubscribe("IoT/"+acquariumcode+"/control/light")


if __name__=="__main__":
    host = os.environ['CATALOG_HOST']
    port = os.environ['CATALOG_PORT']

    # api_key list to link the aquarium number (1, 2, 3, 4) to its api_key
    # api_key = ["ASGRXGIK2THFOBZC","ASGRXGIK2THFOBZC","ASGRXGIK2THFOBZC","ASGRXGIK2THFOBZC"]

    # topic list to which subscribe
    # topicSub = ["IoT/1/sensors/temperature", "IoT/1/sensors/waterlevel", "IoT/1/sensors/light", "IoT/1/sensors/feed",
    # "IoT/2/sensors/temperature", "IoT/2/sensors/waterlevel", "IoT/2/sensors/ligh", "IoT/2/sensors/feed",
    # "IoT/3/sensors/temperature", "IoT/3/sensors/waterlevel", "IoT/3/sensors/ligh", "IoT/3/sensors/feed",
    # "IoT/4/sensors/temperature", "IoT/4/sensors/waterlevel", "IoT/4/sensors/ligh", "IoT/4/sensors/feed"]

    AdaptorPublisher = PostValueThingspeak("ThingSpeak1234", "mqtt.eclipseprojects.io", host, port)
    AdaptorPublisher.startOperation()

    while True:
        time.sleep(0.1)
        