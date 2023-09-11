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


class EchoBot:
    def __init__(self, token):
        # Local token
        self.tokenBot = token
        # Catalog token
        # self.tokenBot=requests.get("http://catalogIP/telegram_token").json()["telegramToken"]
        self.bot = telepot.Bot(self.tokenBot)
        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()
        self.client = MyMQTT("smart_aqu_bot", broker, port, None)

    def on_chat_message(self, msg):
        content_type, chat_type, chat_ID = telepot.glance(msg)
        message = msg['text']
        self.bot.sendMessage(chat_ID, text = "You sent:\n"+message)

class StatisticsControlBot:
    def __init__(self, token, broker, port, topic_statisticsS, topic_statisticsP):
        self.tokenBot = token
        self.bot = telepot.Bot(self.tokenBot)
        self.client = MyMQTT("smart_aqu_bot", broker, port, self)
        self.client.start()
        self.topics = topic_statisticsS
        self.topicp = topic_statisticsP
        self.first_connection = True
        self.request = {"chat_ID": None, "bool": False, "type": None}

        self.__message = {'bn': "smart_aqu_bot",
                          'e': [{'n': 'statistics', 'v': '', 't': '', 'u': 'bool'}]}
        
        self.light_on_time = []
        self.light_off_time = []
        MessageLoop(self.bot, {'chat': self.on_chat_message,
                               'callback_query': self.on_callback_query}).run_as_thread()

    def on_chat_message(self, msg):
        content_type, chat_type, chat_ID = telepot.glance(msg)
        message = msg['text']
        
        if (self.first_connection == True):
            self.chatID = msg
            self.client.mySubscribe(self.topics)
            self.first_connection = False

        if self.client:
            # If MQTT client is connected and it requests for statistics, the BOT sends a message askying for which type of statistics analysis
            if message == "/statistics": 
                buttons = [[InlineKeyboardButton(text = f'LIGHT 💡', callback_data = f'light'), 
                    InlineKeyboardButton(text = f'TEMPERATURE 🌡', callback_data = f'temperature'),
                    InlineKeyboardButton(text = f'WATER LEVEL 🌊', callback_data = f'waterlevel')
                    ]]
                keyboard = InlineKeyboardMarkup(inline_keyboard = buttons)
                self.bot.sendMessage(chat_ID, text = 'Which statistics do you want to see?', reply_markup = keyboard)
            elif message.isdigit() and self.request["bool"]:
                # The BOT retreives the data for statistical analysis days requested
                days = int(message)
                msg = {"days": days, "type": self.request["type"]}
                self.client.myPublish(self.topicp[self.request["type"]], msg)
                self.bot.sendMessage(chat_ID, text = f"Requested statistics for {days} days.")
            else:
                self.bot.sendMessage(chat_ID, text = "Command not supported!")
        else:
            print("STATISTIC BOT MQTT client is not connected.")

    def on_callback_query(self, msg):
        query_id, chat_ID, query_data = telepot.glance(msg, flavor = 'callback_query')
        chat_id = msg['message']['chat']['id']
        self.request["chat_ID"] = chat_ID
        
        if query_data == 'light':
            self.request_days_input(chat_id, 'light')
            self.request["bool"] = True
            self.request["type"] = "light"
        elif query_data == 'temperature':
            self.request_days_input(chat_id, 'temperature')
            self.request["bool"] = True
            self.request["type"] = "temperature"
        elif query_data == 'waterlevel':
            self.request_days_input(chat_id, 'waterlevel')
            self.request["bool"] = True
            self.request["type"] = "waterlevel"
        else:
            self.bot.sendMessage(chat_id, text = "Invalid option")

    def request_days_input(self, chat_id, control_type):
        message_to_send = f"Please enter the number of days for {control_type} statistics.\nYou can type the number directly. Example: 7"
        self.bot.sendMessage(chat_id, text = message_to_send)       
        
    def notify(self, topics, payload):
        print(f"STATISTIC BOT Notifying payload {payload}")

        self.set = json.loads(payload)
        answer = "The maximum was "+str(self.set["maximum values"])+ "\nThe minimum was "+ str(self.set["minimum values"])+"\nThe average was "+str(self.set["average"])
        self.bot.sendMessage(self.request["chat_ID"], text = answer)

        if self.request["type"] == "light":
            self.bot.sendMessage(self.request["chat_ID"], text = "The cost is"+str(self.set["average cost"]))

        self.request["bool"] = False
        self.request["type"] = None
        self.request["chat_ID"] = None


if __name__ == "__main__":
    conf = json.load(open("settings.json"))
    token = conf["telegramToken"]

    # SimpleSwitchBot
    broker = conf["brokerIP"]
    port = conf["brokerPort"]
    topic = conf["mqttTopic"]
    topics = "IoT/1/telegram/statistics"
    topicp = {"temperature":"IoT/statics/temperature","waterlevel":"IoT/statics/waterlevel", "light":"IoT/statics/light"}

    stcb = StatisticsControlBot(token, broker, port, topics,topicp)

    while True:
        time.sleep(3)