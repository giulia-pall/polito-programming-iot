import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
import time
from MyMQTT import *
import datetime


class WaterLevelControlBot:
    def __init__(self, topics):
        self.previous_status = {}
        self.current_status = {}
        self.topic_waterlevel = {}

        for i in topics.keys():
            self.topic_waterlevel[i] = topics[i]["topic_waterlevel"]
            self.previous_status[i] = None
            self.current_status[i] = None

        self.__message = {'bn': "smart_aqu_bot",
                          'e': [{'n': 'waterlevel', 'v': '', 't': '', 'u': 'bool','l': ''}]}

    def on_chat_message(self, aquarium_code):
        aquarium_code = str(aquarium_code)
        if self.current_status[aquarium_code] == "ok":
            return("There is still ENOUGH water in the aquarium." )
        elif self.current_status[aquarium_code] == "low":
           return("The water level in the aquarium is LOW. You need to fill it!" )
        elif self.current_status[aquarium_code] == "too low":
            return("The water level in the aquarium is TOO LOW. Fill it as soon as possible!" )

    def notify(self, payload, aquarium_code):
        # This function activates when a message arrives on the topic
        print(f"WATER LEVEL BOT Notifying on aquarium {aquarium_code} with payload {payload}")

        self.set = payload
        msg = None

        self.current_status[aquarium_code] = payload["e"][0]["l"]

        if len(self.previous_status.keys()) < int(aquarium_code):
            self.previous_status[aquarium_code] = 0
       
        if  self.previous_status[aquarium_code] != self.current_status[aquarium_code]:
            if self.current_status[aquarium_code] == "low":
                msg="The water level in the aquarium is LOW. Fill it!" 
            elif self.current_status[aquarium_code] == "too low":
               msg="The water level in the aquarium is TOO LOW. Fill it as soon as possible!" 
    
        self.previous_status[aquarium_code] = self.current_status[aquarium_code]

        return msg
