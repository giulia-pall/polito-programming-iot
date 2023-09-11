import os
import paho.mqtt.client as PahoMQTT
import json
import time
from MyMQTT import *
import requests


class LightControl:
    def __init__(self, ClientID, broker, host, port):
        self.clientID = ClientID
        self.broker = broker
        self.host = host
        self.port = port
        time.sleep(3)       
        self.light = {}
        self.client = MyMQTT(self.clientID, self.broker, 1883, self)
        self.topic_add, self.topicp, self.topics = self.initialize(host, port)
        self.client.start()
        self.level = {}
        self.level_min = 400
        self.level_max = 600
        self.message = {"bn": "IoT/control/light", "e": [{"n": "light", "v": None, "t": time.time(), "u": "bool", "l":"bool"}]}

    def startOperation(self):
        self.client.mySubscribe(self.topic_add)
        for i in self.topics:
            self.client.mySubscribe(i)

    def notify(self, topics, payload):
        print(f"LIGHT Notifying on {topics} with payload {payload}")

        if topics == self.topic_add:
            self.addnewaquarium(json.loads(payload))
        aquarium_code = topics[4:5]
        for i in range(len(self.topicp)):
            if self.topicp[i][4] == aquarium_code:
                topic_publisher = self.topicp[i]
                self.level[aquarium_code] = json.loads(payload)
                self.light [aquarium_code] = self.level[aquarium_code]["e"][0]["v"]
                if int(self.light[aquarium_code]) < self.level_min:
                    print("LIGHT level is LOW!")
                    self.publishControl(topic_publisher,{"bn": self.topicp, "aquarium": aquarium_code, "e": [{"n": "light", "v": self.light[aquarium_code], "t": time.time(),"u": "bool", "l":1}]})
                elif int(self.light[aquarium_code]) > self.level_max:
                    print("LIGHT level HIGH!") 
                    self.publishControl(topic_publisher,{"bn": self.topicp, "aquarium": aquarium_code, "e": [{"n": "light", "v": self.light[aquarium_code], "t": time.time(),"u": "bool", "l":0}]})

    def publishControl(self, topic, msg):
        print(f"LIGHT Publishing on {topic} with msg {msg}")
        # It publish 0 for OFF status and 1 for ON status
        self.client.myPublish(topic,msg)

    def initialize(self, host, port):
        # Initializing light topics from catalog

        catalog = requests.get( "http://"+self.host+":"+str(self.port)+"/service").json()
        controllersList = catalog["controllersList"]
        topic_add = catalog["topicAdd"]
        
        name = "LightSwitch"
        topicp = []
        topics = []
        
        for i in controllersList.keys():
            if controllersList[i]["name"] == name:
                for j in controllersList[i]["topics"]:
                    if j["type"] == "Subscriber":
                        topics.append(j["topic"])
                    elif j["type"] == "Publisher":
                        topicp.append(j["topic"])

        return  topic_add, topicp, topics

    def addnewaquarium(self, message):
        # Add new aquarium to light control

        aquarium_code = int(message)
        catalog = requests.get("http://"+self.host+":"+str(self.port)+"/service").json() 
        controllersList = catalog["controllersList"]
        name = "LightSwitch"

        for i in controllersList.keys():           
            if controllersList[i]["name"] == name and controllersList[i]["aquariumID"] == aquarium_code:
                for j in controllersList[i]["topics"]:
                    if j["type"] == "Subscriber":
                        self.topics.append(j["topic"])
                        self.client.mySubscribe(j["topic"])
                    elif j["type"] == "Publisher":
                        self.topicp.append(j["topic"])


if __name__=="__main__":
    host = os.environ['CATALOG_HOST']
    port = os.environ['CATALOG_PORT']

    light = LightControl("Alex999sf7ds77654", "mqtt.eclipseprojects.io", host, port)
    light.startOperation()
    
    while True:
        time.sleep(10)
