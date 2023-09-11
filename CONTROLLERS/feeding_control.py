import os
import paho.mqtt.client as PahoMQTT
import json
import time
from MyMQTT import *
import requests


class FeedingControl:
    def __init__(self, ClientID, broker, host, port):
        # self.set = json.load(open('feeding_setting.json'))
        self.messageReceived = {}
        self.host = host
        self.port = port
        self.clientID = ClientID
        self.broker = broker
        self.client = MyMQTT(self.clientID,self.broker,1883,self)
        self.client.start()
        time.sleep(3)
        self.topic_add, self.topicS, self.topicR, self.topic_settings, self.button = self.initialize(host, port)

        # Printing valuable information
        # print(self.topic_settings)
        # print(self.topic_add)
        # print("send")
        # print(self.topicS)
        # print(self.topicR)

        self.message = {"bn": "smart_aqu_bot", "e": [{"n": "feed", "v": 0, "t": "", "u": "bool"}]}
        self.timetable = []
        self.cyclical_schedule = []
        self.last_warning = []
        self.is_feeding_set = []
        self.initializevariable()

    def initializevariable(self):
        # Initializing feeding settings (time and schedule) from catalog data

        catalog = requests.get("http://"+host+":"+str(port)+"/service").json()
        aquarium_list = catalog["aquariumList"]
        for i in aquarium_list.keys():
            if aquarium_list[i]["changed"] == True:
                self.timetable.append({"aquarium_code": i, "time": aquarium_list[i]["feedTime"]})
                self.cyclical_schedule.append({"aquarium_code": i, "schedule": aquarium_list[i]["feedSchedule"]})
                self.is_feeding_set.append({"aquarium_code": i, "is_feeding_set": True})
                self.last_warning.append({"aquarium_code": i, "last_warning": "00:00"})
        
    def startOperation(self):
        self.client.mySubscribe(self.topic_add)
        for i in range(len(self.topicR)):
            self.client.mySubscribe(self.topicR[i])
        for i in range(len(self.topic_settings)):
            self.client.mySubscribe(self.topic_settings[i])
        
    
    def notify(self, topicR, payload):
        # When telegram sends the message with the settings, it updates them and saves them on setting files
        # Controller receives on topicR only the time with HH:MM format as a json
        print(f"FEEDING Notifying on {topicR} with payload {payload}")

        aquarium_code = topicR[4:5]
        self.messageReceived = json.loads(payload)

        if topicR == self.topic_add:
            self.addnewaquarium(self.messageReceived)
        elif  topicR[-8:] == "settings":
            time_table = (self.messageReceived["e"][0]["timetable"])          
            cyclical_schedule = self.messageReceived["e"][0]["cyclical_schedule"]
            settings = True
            self.save_configurations(time_table, cyclical_schedule, settings, aquarium_code)
        else:
            print(f"FEEDING Feeding staus is: {self.button}")

            for i in range(len(self.button)):
                if self.button[i]["aquarium_code"] == aquarium_code:
                    self.button[i]["status"] = 1
    
    def publishwarning(self, msg, aquarium_code):
        # Sending message to telegram 

        print(f"FEEDING Publishing warning on {self.topicS} with msg: {msg}")

        #self.message["e"][0]["t"] = str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min)

        for i in self.topicS:
            if i == "IoT/"+str(aquarium_code)+"/control/feeding":
                print("FEEDING Message sent!")
                self.client.myPublish(i, msg)

    def initialize(self, host, port):
        # Initializing topic and feeding status from catalog data

        catalog = requests.get("http://"+host+":"+str(port)+"/service").json()
        controllersList = catalog["controllersList"]
        aquariumList = catalog["aquariumList"]
        topic_add = catalog["topicAdd"]
        self.client.mySubscribe(topic_add)
        name = "FeedingControl"
        topicp = []
        topics = []
        button = []
        topic_settings = []

        for i in aquariumList.keys():
            button.append({"aquarium_code": i, "status": 1})
        for i in controllersList.keys():
            if controllersList[i]["name"] == name:
                for j in controllersList[i]["topics"]:
                    if j["type"] == "Subscriber":
                        self.client.mySubscribe(j["topic"])
                        if j["topic"][-8:] == "settings":
                            topic_settings.append(j["topic"])
                        else:
                            topics.append(j["topic"])
                    else:
                        topicp.append(j["topic"])

        return  topic_add, topicp, topics, topic_settings, button
    
    def save_configurations(self, time_table, cyclical_schedule, settings, aquarium_code):
        # Save configuration for feeding on catalog through a POST request

        print("FEEDING Saving the configuration")

        catalog = requests.get("http://"+host+":"+str(port)+"/service").json()
        aquarium_list = catalog["aquariumList"]

        for i in aquarium_list.keys():
            if aquarium_list[i]["aquariumID"] == int(aquarium_code):
                aquarium_list[i]["feedTime"] = time_table
                aquarium_list[i]["feedSchedule"] = cyclical_schedule
                aquarium_list[i]["changed"] = settings

        catalog["aquariumList"] = aquarium_list
        requests.post("http://"+host+":"+str(port)+"/service", catalog)

        self.timetable[int(aquarium_code)-1] = ({"aquarium_code": aquarium_code, "time": time_table})
        self.cyclical_schedule[int(aquarium_code)-1] = ({"aquarium_code": aquarium_code, "schedule": cyclical_schedule})
        self.last_warning[int(aquarium_code)-1] = ({"aquarium_code": aquarium_code, "last_warning": "00:00"})
        self.is_feeding_set[int(aquarium_code)-1] = ({"aquarium_code": aquarium_code, "is_feeding_set": True})

    def check_time(self):
        if time.localtime().tm_min < 10:
            currentTime = str(time.localtime().tm_hour) + ":0" + str(time.localtime().tm_min)
        else:
            currentTime = str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min)
        if time.localtime().tm_hour < 10:
            currentTime = str(0)+currentTime
        for i in range(len(self.timetable)):
            print(f"FEEDING Current time is {currentTime}, timetable is {self.timetable[i]['time']}")
            aquarium_code = self.timetable[i]["aquarium_code"]
            if currentTime == "00:00":  
                self.button[i]["status"] = 1
            print(f"FEEDING Feeding set: {self.is_feeding_set}")

            # If the time is the same as the one in setting, I send a msg to telegram and I keep sending it cyclically as cycical set until the button is pushed
            if self.is_feeding_set[i]["is_feeding_set"] == True and self.is_feeding_set[i]["aquarium_code"] == aquarium_code:
                if currentTime == self.timetable[i]["time"]:
                    # Util it is not feeding time it is set to 1, then it is set to 0
                    self.button[i]["status"] = 0    
                if self.button[i]["status"] == 0 and int(time.localtime().tm_hour)*60+int(int(time.localtime().tm_min))-(int(self.last_warning[i]["last_warning"][:2])*60+int(self.last_warning[i]["last_warning"][-2:])) >= self.cyclical_schedule[i]["schedule"]:
                    self.last_warning[i]["last_warning"] = currentTime
                    self.publishwarning({"bn": self.topicS[i], "e": [{"n": "feed", "v": self.button[i]["status"], "t": currentTime, "u": "bool", "timetable": self.timetable[i]["time"], "cyclical_schedule": self.cyclical_schedule[i]["schedule"]}]}, aquarium_code)
                    time.sleep(60)

    def addnewaquarium(self, message):
        # Add new aquarium to feeding control

        aquarium_code = int(message)
        catalog = requests.get("http://"+self.host+":"+str(self.port)+"/service").json() 
        controllersList = catalog["controllersList"]
        name = "FeedingControl"
        self.button.append({"aquarium_code": aquarium_code, "status": 1})

        for i in controllersList.keys():
            if controllersList[i] ["name"] == name and controllersList[i]["aquariumID"] == aquarium_code:
                for j in controllersList[i]["topics"]:
                    if j["type"] == "Subscriber":
                        if j["topic"][-8:] == "settings":
                            self.client.mySubscribe(j["topic"])
                            self.topic_settings.append(j["topic"])
                        else:
                            self.client.mySubscribe(j["topic"])
                            self.topicR.append(j["topic"])
                    else:
                        self.topicS.append(j["topic"])
        
        self.timetable.append({"aquarium_code": aquarium_code, "time": "00:00"})
        self.cyclical_schedule.append({"aquarium_code": aquarium_code, "schedule": 0})
        self.last_warning.append({"aquarium_code": aquarium_code, "last_warning": "00:00"})
        self.is_feeding_set.append({"aquarium_code": aquarium_code, "is_feeding_set": False})
        

if __name__=="__main__":
    host = os.environ['CATALOG_HOST']
    port = os.environ['CATALOG_PORT']
        
    telegram = FeedingControl("Alexer999777j654", "mqtt.eclipseprojects.io", host, port)
    telegram.startOperation()

    #button = FeedingControl("Alex92324", "mqtt.eclipseprojects.io", "IoT/sensors/feeding", "IoT/sensors/button")
    #button.startOperation()

    while True:
        telegram.check_time()
        time.sleep(10)
