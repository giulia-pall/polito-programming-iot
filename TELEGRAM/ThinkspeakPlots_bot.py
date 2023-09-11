import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
import requests
import time
from MyMQTT import *
import urllib3
import numpy as np
import datetime
import requests


class ThingSpeakPlots:
    def __init__(self, url):
        self.URL = url
        self.data = {}
        self.initialize()

    def initialize(self):
        catalog = requests.get(self.URL+"/service").json()
        ThingSpeak = catalog["thingspeak"]

        for i in ThingSpeak.keys():
            self.data[i] = ThingSpeak[i]["dashboardURL"]
        
    def on_chat_message(self, aquarium_code): 

        for i in self.data.keys():
            if i==str(aquarium_code):
                return self.data[i]
            
        return None
              
  
