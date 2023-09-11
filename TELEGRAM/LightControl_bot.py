import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
import requests
import time
from MyMQTT import *
import urllib3
import datetime
import threading


class LightControlBot:
    def __init__(self, broker, port, topic_light):
        self.client = MyMQTT("smart_aqu_bot", broker, port, self)
        self.set = {}
        self.topic_light = {}
        self.previous_status = {}
        self.current_status = {}
        self.light_on_time = {}
        self.light_off_time = {}

        for i in topic_light.keys():
            self.topic_light[i] = topic_light[i]["topic_light"]
            self.previous_status[i] = None
            self.light_on_time[i] = []
            self.light_off_time [i] = []

        self.__message = {'bn': "smart_aqu_bot",
                          'e': [{'n': 'light', 'v': '', 't': '', 'u': 'bool'}]}

        # self.subscription_setup(topic_light)

    def on_chat_message(self, aquarium_code):
        #print(self.current_status)
        aquarium_code = str(aquarium_code)
        if self.current_status[aquarium_code] == 1:
            return "The light is ON."
        else:
            return "The light is OFF."
        
    def notify(self, payload, aquarium_code):
        # This function activates when a message arrives on the topic
        print(f"LIGHT BOT Notifying on aquarium {aquarium_code} with payload {payload}")

        aquarium_code = str(aquarium_code)
        self.current_status[aquarium_code] = payload["e"][0]["l"]

        print(f"LIGHT BOT Light current status is {self.current_status}, last status is {self.previous_status}")
     
        if len(self.previous_status.keys()) < int(aquarium_code):
            self.previous_status[aquarium_code] = 0
        if  self.previous_status[aquarium_code] != self.current_status[aquarium_code]:
            self.previous_status[aquarium_code] = self.current_status[aquarium_code]
            time = datetime.datetime.fromtimestamp(int(payload['e'][0]['t']))
            print(f"LIGHT BOT Created at {time.hour}:{time.minute}")
            if self.current_status[aquarium_code] == 1:
                return(f"The light has been switched ON at {time.hour}:{time.minute}")
            elif  self.current_status[aquarium_code] == 0:
                return(f"The light has been switched OFF at {time.hour}:{time.minute}")
        else:
            self.previous_status[aquarium_code] = self.current_status[aquarium_code]
            return None
            