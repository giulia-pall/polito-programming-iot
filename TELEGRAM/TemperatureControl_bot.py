import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
import requests
import time
import paho.mqtt.client as PahoMQTT
from MyMQTT import *
import urllib3
import datetime
import threading


class TemperatureControlBot:
    def __init__(self, topic_temperature):
        self.topic_temperature = {}
        self.set = {}
        self.__message = {'bn': "smart_aqu_bot",
                          'e': [{'n': 'temperature', 'v': '', 't': '', 'u': 'bool', 's': 'bool', 'l': ''}]}
        self.temperature = {}
       
        self.first_connection = {}
        self.previous_status = {} 
        self.current_status = {}

        for i in topic_temperature.keys():
            self.first_connection[i] = 0
            self.previous_status[i] = 0
            self.temperature[i] = 0
            self.topic_temperature[i] = topic_temperature
      
    def on_chat_message(self, aquarium_code):
        aquarium_code = str(aquarium_code)
        if self.current_status[aquarium_code] == "too low": 
            msg = 'The temperature in the aquarium is '+str(self.set['e'][0]['v'])+' °C. The heater is ON.'
        elif self.current_status[aquarium_code] == "too high": 
            msg = 'The temperature in the aquarium is '+str(self.set['e'][0]['v'])+' °C. Please ADD some cold water.'
        elif self.current_status[aquarium_code] == "ok":
            msg = 'The temperature in the aquarium is '+str(self.set['e'][0]['v'])+' °C.'
        else: 
            msg = "Your thermometer is NOT working as expected please contact the assistance!"

        return msg

    def notify(self, payload, aquarium_code):
        # This function activates when a message arrives on the topic
        print(f"TEMPERATURE BOT Notifying on aquarium {aquarium_code} with payload {payload}")

        self.set = payload
        msg = None
        if len(self.previous_status.keys()) < int(aquarium_code):
            self.previous_status[aquarium_code] = 0
        
        self.current_status[aquarium_code] = self.set["e"][0]["l"]
        if  self.previous_status[aquarium_code] != self.current_status[aquarium_code]:
            if self.current_status[aquarium_code] == "too high":
                msg = 'The temperature in the aquarium is '+str(self.set['e'][0]['v'])+' °C. It is TOO HIGH, please ADD some COLD water!'
            elif self.current_status[aquarium_code] == "too low":
                msg = 'The temperature in the aquarium is '+str(self.set['e'][0]['v'])+' °C. The heater was switched ON.'               

        self.previous_status[aquarium_code] = self.current_status[aquarium_code]

        return msg
               