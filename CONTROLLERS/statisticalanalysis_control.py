import os
import paho.mqtt.client as PahoMQTT
import json
import time
from MyMQTT import *
import urllib
import requests


class StatisticLight:
    def __init__(self, ClientID, broker, field, current_cost, host, port, name, sensor):
        self.clientID = ClientID
        self.broker = broker
        self.client = MyMQTT(self.clientID, self.broker, 1883, self)
        self.name = name
        self.sensor = sensor
        self.host = host
        self.port = port
        self.URL = "http://"+self.host+":"+str(self.port)
        #self.apiKey, self.channel = self.initialize_thingspeak()
        self.field = field
        self.light_cost = current_cost
        #self.topic_add, self.topics, self.topicp = self.initialize(self.host, self.port)
    
    def startOperation(self):
        self.client.start()
        time.sleep(3)
        self.channel = self.initialize_thingspeak()
        self.topic_add, self.topics, self.topicp = self.initialize(self.host, self.port)
        #for i in self.topics:
            #self.client.mySubscribe(i)

    def notify(self, topicr, payload):
        # When telegram sends a message with the number of days on which perform the analysis and the time at which feeding the animal, then the functions detData, analysis and publishdata are called
        print(f"STATISTIC LIGHT Notifying on {topicr} with payload {payload}")

        self.msg = json.loads(payload)
        if topicr == self.topic_add:
            self.addnewaquarium(self.msg)
        else:
            self.type = self.msg["type"]
            self.days = self.msg["days"]
            aquarium_code = self.msg["aquarium_code"]
            values_json = self.getData(self.days, aquarium_code)
            [average, max, min, average_cost] = self.analysys(values_json)
            self.publishdata(self.days, average, max, min, average_cost, aquarium_code)

    def getData(self, nDays, aquarium_code):
        # By URL, the data are taken from the plot on thingspeak and they are saved in a variable as in a json format

        days_number = int(nDays)
        baseURL = 'https://api.thingspeak.com/channels/'+self.channel[str(aquarium_code)]+'/fields/3.json?days='+str(days_number)
        
        f = urllib.request.urlopen(baseURL)
        reply = f.read()
        f.close()
        response = json.loads(reply)
        data = response['feeds']

        return data

    def analysys(self, data):
        # Generating the analysis values from the json file retreived

        one_day_flag = 0
        days = 1
        dur_per_day = 0
        cost_per_day = 0
        value = 0
        last_value = 0
        i = 0
        max = 0
        min = 0
        avg_cost = 0
        lightON_duration = 0
        fieldN = "field"+str(self.field)

        while i < len(data):
            value = data[i][fieldN]
            times = data[i]["created_at"]
            date_created = times[0:10]
            time_created = times[11:19]

            if last_value == None:
                last_value = 0
            if value != None:
                if i == 0:
                    if value == 1:
                        startDuration = time_created
                else:
                    if date_created != last_date:
                        # New day
                        one_day_flag = 1
                        days += 1
                        # Updating the duration of the last day
                        if float(last_value) == 1:
                            lightON_duration += 24*60 - (int(last_hour[0:2]) * 60 + int(last_hour[3:5]))
                        if float(value) == 1 and float(last_value) == 0:
                            # The light is ON
                            startDuration = time_created
                        if float(value) == 1 and float(last_value) == 1:
                            # The light was already on from the last day
                            startDuration = "00:00:00"
                        if dur_per_day == 0:
                            min = lightON_duration
                        # Updating max value
                        if max < lightON_duration:
                            max = lightON_duration
                        # Updating min value
                        if min > lightON_duration:
                            min = lightON_duration
                        dur_per_day += lightON_duration
                        cost_per_day += dur_per_day * self.light_cost
                        lightON_duration = 0 
                    else:
                        # Same day
                        if float(value) != float(last_value) and float(last_value) == 0:
                            # The light is ON
                            startDuration = time_created
                        if float(value) != float(last_value) and float(last_value) == 1:
                            # The light is OFF
                            lightON_duration += (int(time_created[0:2]) * 60 + int(time_created[3:5])) - (int(startDuration[0:2]) * 60 + int(startDuration[3:5]))
                        if one_day_flag == 0 and i == (len(data)-1):
                            lightON_duration += (int(time_created[0:2]) * 60 + int(time_created[3:5])) - (int(startDuration[0:2]) * 60 + int(startDuration[3:5]))
                            min = lightON_duration
                            max = lightON_duration
                            dur_per_day += lightON_duration
                            cost_per_day += dur_per_day * self.light_cost

            last_value = value
            last_date = date_created
            last_hour = time_created
            i = i + 1
        average = int(dur_per_day)/int(days)
        avg_cost = cost_per_day/int(days)

        return average, max, min, avg_cost

    def publishdata(self, days, average, max, min, average_cost, aquarium_code):
        # Publish data in json format
    
        msg = {'days' : days,
               'maximum values': max,
               'minimum values': min,
               'average': average,
               'average cost': average_cost,
               'aquarium_code': aquarium_code}
        
        for i in range(len(self.topicp)):
            code = self.topicp[i].split("/")[1]
            if code == aquarium_code:
                print(f"STATISTIC LISGHT Publishing on {self.topicp[i]} with msg {msg}")
                self.client.myPublish(self.topicp[i], msg)
    
    def initialize(self, host, port):
        # Initializing topics from catalog

        catalog = requests.get("http://"+self.host+":"+str(self.port)+"/service").json()
        controllersList = catalog["controllersList"]
        topic_add = catalog["topicAdd"]
        self.client.mySubscribe(topic_add)
        topicp = []
        topics = []

        for i in controllersList.keys():
            if controllersList[i]["name"] == self.name:
                for j in controllersList[i]["topics"]:
                    if j["type"] == "Subscriber":
                        self.client.mySubscribe(j["topic"]+self.sensor)
                        topics.append(j["topic"]+self.sensor)
                    else:
                        topicp.append(j["topic"])

        return topic_add, topics, topicp
    
    def addnewaquarium(self, message):
        # Add new aquarium to control

        aquarium_code = int(message)
        catalog = requests.get("http://"+self.host+":"+str(self.port)+"/service").json() 
        controllersList = catalog["controllersList"]
        for i in controllersList.keys():
            if controllersList[i]["name"] == self.name and controllersList[i]["aquariumID"] == aquarium_code:
                for j in controllersList[i]["topics"]:
                    if j["type"] == "Subscriber":
                        self.topics.append(j["topic"]+self.sensor)
                        self.client.mySubscribe(j["topic"]+self.sensor)
                    else:
                        self.topicp.append(j["topic"])

    def initialize_thingspeak(self):
        # Initializing thingspeak channel from catalog data

        catalog = requests.get(self.URL+"/service").json()
        Thingspeak = catalog["thingspeak"]                                                             
        channel = {}

        for i in Thingspeak.keys():
            channel[i] = Thingspeak[i]["channel"]

        return channel


class Statistics:
    def __init__(self, ClientID, broker, field, host, port, name, sensor):
        self.clientID = ClientID
        self.broker = broker
        self.client = MyMQTT(self.clientID,self.broker,1883,self)
        self.name = name
        self.sensor = sensor
        self.host = host
        self.port = port
        self.URL = "http://"+self.host+":"+str(self.port)
        #self.apiKey, self.channel = self.initialize_thingspeak()
        self.field = field
        #self.topic_add, self.topics, self.topicp = self.initialize(self.host, self.port)

    def startOperation(self):
        self.client.start()
        time.sleep(3)
        self.channel = self.initialize_thingspeak()
        self.topic_add, self.topics, self.topicp = self.initialize(self.host, self.port)
        #for i in self.topics:
            #self.client.mySubscribe(i)

    def notify(self, topicr, payload):
        # When telegram sends a message with the number of days on which performing the analysis, functions getData, analysys and publishdata are called   
        print(f"STATISTICS Notifying on {topicr} with payload {payload}")

        self.msg = json.loads(payload)

        if topicr == self.topic_add:
            self.addnewaquarium(self.msg)
        else:        
            self.type = self.msg["type"]
            self.days = self.msg["days"]
            aquarium_code = self.msg["aquarium_code"]
            values_json = self.getData(self.days, aquarium_code)
            [average, max, min] = self.analysys(values_json)    
            self.publishdata(average, max, min, self.days, aquarium_code)

    def getData(self, nDays, aquarium_code):
        # By URL, data are taken from the plot on thingspeak and they are saved in a variable in json format 
    
        days_number = int(nDays)
        if self.field == "1":
            baseURL = 'https://api.thingspeak.com/channels/'+self.channel[str(aquarium_code)]+'/fields/1.json?days='+str(days_number)
            print(f"STATISTIC BaseURL Thingspeak is {baseURL}")
        elif self.field == "2":
            baseURL = 'https://api.thingspeak.com/channels/'+self.channel[str(aquarium_code)]+'/fields/2.json?days='+str(days_number)
            print(f"STATISTIC BaseURL Thingspeak is {baseURL}")

        f = urllib.request.urlopen(baseURL)
        reply = f.read()
        f.close()
        response = json.loads(reply)
        data = response["feeds"]

        return data

    def analysys(self, data):
        # Geneating the analysis values from the json file retreived
    
        i = 0
        average = 0
        max = 0
        min = 0
        
        fieldN = "field" + str(self.field)
        
        while i < len(data):
            if float(data[i][fieldN] != None):
                value = float(data[i][fieldN])
                average += value
                if max < value:
                    max = value
                if i == 0:
                    min = value
                elif min > value:
                    min = value
            i+=1
        
        average = average/len(data)
        
        return average, max, min

    def publishdata(self, average, max, min, days, aquarium_code):
        # Publishing data in json format
    
        msg = {'days': days,
               'maximum values': max,
               'minimum values': min,
               'average': average,
               'aquarium_code': aquarium_code}
        
        for i in range(len(self.topicp)):
            code = self.topicp[i].split("/")[1]
            if code == aquarium_code:
                print(f"STATISTICS Publishing data on {self.topicp[i]} with msg {msg}")
                self.client.myPublish(self.topicp[i], msg)
    
    def initialize(self, host, port):
        # Initializing statistics topic from catalog data

        print("http://" + host+":" + str(port) + "/service")
        catalog = requests.get("http://" + self.host + ":" + str(self.port) + "/service").json()
        controllersList = catalog["controllersList"]
        topic_add = catalog["topicAdd"]
        self.client.mySubscribe(topic_add)
        topicp = []
        topics = []

        for i in controllersList.keys():
            if controllersList[i]["name"] == self.name:
                for j in controllersList[i]["topics"]:
                    if j["type"] == "Subscriber":
                        self.client.mySubscribe(j["topic"] + self.sensor)
                        topics.append(j["topic"] + self.sensor)
                    else:
                        topicp.append(j["topic"])

        return topic_add, topics, topicp
    
    def addnewaquarium(self, message):
        # Add new aquarium to control

        aquarium_code = int(message)
        catalog = requests.get("http://" + self.host + ":" + str(self.port) + "/service").json() 
        controllersList = catalog["controllersList"]

        for i in controllersList.keys():
            if controllersList[i]["name"] == self.name and controllersList[i]["aquariumID"] == aquarium_code:
                for j in controllersList[i]["topics"]:
                    if j["type"] == "Subscriber":
                        self.topics.append(j["topic"] + self.sensor)
                        self.client.mySubscribe(j["topic"] + self.sensor)
                    else:
                        self.topicp.append(j["topic"])
                        
    def initialize_thingspeak(self):
        # Initializing thingspeak channel from catalog data

        catalog = requests.get(self.URL + "/service").json()
        Thingspeak = catalog["thingspeak"]                                                            
        channel = {}
        for i in Thingspeak.keys():
            channel[i] = Thingspeak[i]["channel"]

        return channel


if __name__=="__main__":
    # channel, field e apiKey are thingspeak data
    host = os.environ['CATALOG_HOST']
    port = os.environ['CATALOG_PORT']

    waterlevel = Statistics("waterLevel7890", "mqtt.eclipseprojects.io", "2", host, port, "StatisticalControl", "/waterlevel")
    waterlevel.startOperation()

    temperature = Statistics("temperature7890","mqtt.eclipseprojects.io", "1", host, port, "StatisticalControl", "/temperature")
    temperature.startOperation()

    light = StatisticLight("light789'","mqtt.eclipseprojects.io", "3", 5, host, port, "StatisticalControl", "/light")
    light.startOperation()

    while True:
        time.sleep(10)
        