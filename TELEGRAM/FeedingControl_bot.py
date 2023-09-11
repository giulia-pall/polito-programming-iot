import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
import time
from MyMQTT import *
import datetime
import requests


class FeedingControlBot:
    def __init__(self):
        self.topic_feedingP = {}
        self.topic_feedingS = {}
        self.set = {}
        self.chatID = {}
        self.__message = {'bn': "smart_aqu_bot",
                          'e': [{'n': 'feed', 'v': 0, 't': '', 'u': 'bool'}]}
        self.feeding_time = {}
        self.notification_schedule={}
        self.is_feed_time_set = {}
        self.last_feeding_time = {}
        self.first_connection = {}

        self.current_status = {"1": "12:00"}
        self.last_status = {}

        self.previous_status = {}

    def on_chat_message(self, aquarium_code):
        aquarium_code = str(aquarium_code)
        if self.current_status[aquarium_code] == 0:
            msg = "It's time to feed the animal!"
        elif self.current_status[aquarium_code]== 1:
            msg = "It's NOT time to feed the animal yet! You fed it at {}".format(self.last_feeding_time[aquarium_code])
        else:
            msg = None

        return msg

    def notify(self, payload, aquarium_code): 
        # When a message arrives on the topic, this function activates
        print(f"FEEDING BOT Notifying on aquarium {aquarium_code} with payload {payload}")

        aquarium_code = str(aquarium_code)
        self.set = payload
        
        self.last_status[aquarium_code] = self.current_status[aquarium_code]
        self.current_status[aquarium_code] = self.set["e"][0]["v"]
        print(f"FEEDING BOT Feed current status is {self.current_status}, last status is {self.last_status}")

        msg = None
        if self.current_status[aquarium_code] == 0 :
            msg = "It's time to feed the animal!" 
        elif self.last_status[aquarium_code] == 0 and self.current_status[aquarium_code] == 1:
            self.last_feeding_time[aquarium_code] = self.set['e'][0]['t']
            msg = None

        return msg
    
    def configureaquarium(self, chatID, feeding_time, topicS, topicP, notification, aquarium_code, url):
        aquarium_code = str(aquarium_code)
        self.topic_feedingP[aquarium_code] = topicP
        self.topic_feedingS[aquarium_code] = topicS
        self.chatID[aquarium_code] = []

        self.chatID[aquarium_code].append(chatID)
        self.notification_schedule[aquarium_code] = notification
        self.feeding_time[aquarium_code] = feeding_time
        self.is_feed_time_set [aquarium_code] = True

        self.last_feeding_time[aquarium_code] = "00:00"
        self.first_connection[aquarium_code] = False
        self.current_status[aquarium_code]=0
        self.previous_status[aquarium_code] = 0

        catalog = requests.get(url+"/service").json()
        ID_aquarium = catalog["aquariumList"]
        ID_aquarium[aquarium_code]["feedTime"] = feeding_time
        ID_aquarium[aquarium_code]["feedSchedule"] = self.notification_schedule
        ID_aquarium[aquarium_code]["changed"] = True

        requests.delete(f"{url}/{aquarium_code}")
        requests.post(f"{url}/aquarium", json = ID_aquarium[aquarium_code])

