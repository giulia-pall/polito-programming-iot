import os
import paho.mqtt.client as PahoMQTT
import json
import time
from MyMQTT import *
import requests


class TemperatureControl:
    def __init__(self, ClientID, broker, host, port):
        self.clientID = ClientID
        self.broker = broker
        self.host = host
        self.port = port
        time.sleep(2)
        self.client = MyMQTT(self.clientID, self.broker, 1883, self)        
        self.topic_add, self.topics, self.topicp = self.initialize(self.host, self.port)
        self.level = {}
        self.status = {}
        self.temperature = {}

    def startOperation(self):
        self.client.start()
        self.client.mySubscribe(self.topic_add)
        time.sleep(3)
        for i in self.topics:
            self.client.mySubscribe(i)
   
    def notify(self, topics, payload):
        print(f"TEMPERATURE Notifying on {topics} with payload {payload}")

        if topics == self.topic_add:
            self.addnewaquarium(json.loads(payload))
        else:
            aquarium_code = topics[4:5]
            self.status[str(aquarium_code)] = 0
            self.level[aquarium_code] = json.loads(payload)
            self.temperature[aquarium_code] = self.level[aquarium_code]["e"][0]["v"]

            for i in range(len(self.topicp)):
                print(f"TEMPERATURE Temperature value is: {self.temperature[aquarium_code]}")
                if self.topicp[i][4] == aquarium_code:
                    topic_publisher = self.topicp[i]
                    if int(self.temperature[aquarium_code]) < 25:
                        self.status[aquarium_code] = 1
                        self.publishwarning(topic_publisher, {"bn": self.topicp, "aquarium_code": aquarium_code, "e": [{"n": "temperature", "u": "Cel", "t": time.time(), "v": self.temperature[aquarium_code], "s": self.status, "l": "too low", "b": 1}]})
                    elif int(self.temperature[aquarium_code]) > 27:
                        self.status[aquarium_code] = 0
                        self.publishwarning(topic_publisher, {"bn": self.topicp, "aquarium_code": aquarium_code, "e": [{"n": "temperature", "u": "Cel", "t": time.time(),"v": self.temperature[aquarium_code], "s": self.status, "l": "too high", "b": 0}]})
                    else:
                        if int(self.temperature[aquarium_code]) < 35 and int(self.temperature[aquarium_code]) > 27:
                            if self.status[aquarium_code] == 1:
                                self.status[aquarium_code] = 0
                        self.publishwarning(topic_publisher, {"bn": self.topicp, "aquarium_code": aquarium_code, "e": [{"n": "temperature","u": "Cel", "t": time.time(), "v": self.temperature[aquarium_code], "s": self.status, "l": "ok", "b": 0}]})
                            
    def publishwarning(self, topic, msg):
        print(f"TEMPERATURE Publishing warning on {topic} with msg {msg}")
        self.client.myPublish(topic, msg)

    def initialize(self, host, port):
        # Initializing temperature control topic from catalog data

        catalog = requests.get("http://" + self.host + ":" + str(self.port) + "/service").json() 
        controllersList = catalog["controllersList"]
        topic_add = catalog["topicAdd"]
        name = "Heater"
        topicp = []
        topics = []

        for i in controllersList.keys():
            if controllersList[i]["name"] == name:
                for j in controllersList[i]["topics"]:
                    if j["type"] == "Subscriber":
                        topics.append(j["topic"])
                    else:
                        topicp.append(j["topic"])

        return topic_add, topics, topicp

    def addnewaquarium(self,message):
        # Add new aquarium to temperature control
        
        aquarium_code = int(message)
        catalog = requests.get("http://" + self.host + ":" + str(self.port) + "/service").json() 
        controllersList = catalog["controllersList"]
        name = "Heater"

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

    heater = TemperatureControl("Alex99dfhgcf", "mqtt.eclipseprojects.io", host, port)
    heater.startOperation()
   
    while True:
        time.sleep(10)
