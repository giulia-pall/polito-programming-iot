import os
import paho.mqtt.client as PahoMQTT
import json
import time
import requests
from MyMQTT import *


class WaterLevelControl:
    def __init__(self, ClientID, broker, host, port):
        self.clientID = ClientID
        self.broker = broker
        self.host = host
        self.port = port
        self.client = MyMQTT(self.clientID, self.broker, 1883, self)
        time.sleep(2)
        self.topic_add, self.topics, self.topicp = self.initialize(host, port)
        self.level = {}

    def startOperation(self):
        self.client.start()
        self.client.mySubscribe(self.topic_add)
        time.sleep(3)
        for i in self.topics:
            self.client.mySubscribe(i)
        
    def notify(self, topics, payload):
        print(f"WATER LEVEL Notifying on {topics} with payload {payload}")

        if topics == self.topic_add:
            self.addnewaquarium(json.loads(payload))
        else:
            aquarium_code = topics[4]
            self.level[aquarium_code] = json.loads(payload)
            for i in range(len(self.topicp)):
                if self.topicp[i][4] == aquarium_code:
                    topic_publisher = self.topicp[i]
                    if int(self.level[aquarium_code]["e"][0]["v"]) < 50:                
                        self.publishwarning(topic_publisher, {"bn": topic_publisher, "e": [{"n": "waterlevel", "u": "V", "t": time.time(), "v": self.level[aquarium_code]["e"][0]["v"], "l": "too low"}]})
                    elif int(self.level[aquarium_code]["e"][0]["v"]) <= 300 and int(self.level[aquarium_code]["e"][0]["v"]) >= 250:
                        self.publishwarning(topic_publisher, {"bn": topic_publisher, "e": [{"n": "waterlevel", "u": "V", "t": time.time(), "v": self.level[aquarium_code]["e"][0]["v"], "l": "low"}]})
                    else  :
                        self.publishwarning(topic_publisher, {"bn": topic_publisher, "e": [{"n": "waterlevel", "u": "V", "t": time.time(), "v": self.level[aquarium_code]["e"][0]["v"], "l": "ok"}]})
                
    def publishwarning(self, topic, msg):
        print(f"WATER LEVEL Publishing warning on {topic} with msg {msg}")
        self.client.myPublish(topic, msg)

    def initialize(self, host, port):
        # Initializing water level topics from catalog data

        catalog = requests.get("http://" + host + ":" + str(port) + "/service").json() 
        controllersList = catalog["controllersList"]
        topic_add = catalog["topicAdd"]
        name = "WaterLevelControl"
        topicp = []
        topics = []
        
        for i in controllersList.keys():
            if controllersList[i]["name"] == name:
                for j in controllersList[i]["topics"]:
                    if j["type"] == "Subscriber":
                        topics.append(j["topic"])
                    else:
                        topicp.append(j["topic"])

        return  topic_add, topics, topicp
                     
    def addnewaquarium(self, message):
        # Add new aquarium to water level control
        
        aquarium_code = int(message)
        catalog = requests.get("http://" + self.host + ":" + str(self.port) + "/service").json()
        controllersList = catalog["controllersList"]
        name = "WaterLevelControl"

        for i in controllersList.keys():
            if controllersList[i]["name"] == name and controllersList[i]["aquariumID"] == aquarium_code:
                for j in controllersList[i]["topics"]:
                    if j["type"] == "Subscriber":
                        self.topics.append(j["topic"])
                        self.client.mySubscribe(j["topic"])
                    else:
                        self.topicp.append(j["topic"])
    

if __name__=="__main__":
    host = os.environ['CATALOG_HOST']
    port = os.environ['CATALOG_PORT']
    
    wlc = WaterLevelControl("Alex99sff9777654", "mqtt.eclipseprojects.io", host, port)
    wlc.startOperation()

    while True:
        time.sleep(10)
