#from linecache import _ModuleGlobals
import os
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
import time
from MyMQTT import *
import datetime
import LightControl_bot
import FeedingControl_bot 
import WaterLevelControl_bot
import TemperatureControl_bot
import ThinkspeakPlots_bot
import requests


class EchoBot:
    def __init__(self, token):
        # Local token
        self.tokenBot = token
        # Catalog token
        # self.tokenBot=requests.get("http://catalogIP/telegram_token").json()["telegramToken"]
        self.bot = telepot.Bot(self.tokenBot)
        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()
        self.client = MyMQTT("smart_aqu_bot", broker, port, self)

    def on_chat_message(self, msg):
        content_type, chat_type, chat_ID = telepot.glance(msg)
        message = msg['text']
        self.bot.sendMessage(chat_ID, text="You sent:\n"+message)


class TelegramChatBot:
    CATALOG_HOST = os.environ['CATALOG_HOST']
    CATALOG_PORT = os.environ['CATALOG_PORT']
    CATALOG_URL = f'http://{CATALOG_HOST}:{CATALOG_PORT}'
    
    def __init__(self, token, broker, port, topics, aquarium_code):
        self.broker = broker
        self.port = port
        self.URL = (self.CATALOG_URL) #URL to access catalog
        self._aquarium_number = 0
        self.tokenBot = token
        self.bot = telepot.Bot(self.tokenBot)
        self.chatID = {}
        self.first_connection = {aquarium_code: True}
        self.topics = topics

        MessageLoop(self.bot, {'chat': self.on_chat_message,
                               'notify': self.notify,
                               'callback_query': self.on_callback_query
                               }).run_as_thread()
        
        self.previous_status = None
        self.light = LightControl_bot.LightControlBot(broker,port,self.topics)
        self.waterlevel = WaterLevelControl_bot.WaterLevelControlBot(self.topics)
        self.temperature = TemperatureControl_bot.TemperatureControlBot(self.topics)
        self.thingspeak = ThinkspeakPlots_bot.ThingSpeakPlots(self.URL)
        self.feeding = FeedingControl_bot.FeedingControlBot()
        
        self.is_feed_time_set = {}
        self.is_cyclicalschedule_set = {}
        self.setupvariables()

        self.client = MyMQTT("smart_aqu_bot", broker, port, self)
        self.client.start()

        self.subscription_setup(self.topics, broker, port)
        self.request = {}

    def on_chat_message(self, msg):
        content_type, chat_type, chat_ID = telepot.glance(msg)
        message = msg['text']
        newuser_command = "/newuser"
        newaquarium_command = "/newaquarium"
        
        if (self.check_ID(chat_ID) is None) and (not(message.startswith(newuser_command) or message.startswith(newaquarium_command))):
            # If the chat_ID is not found and a command different from /newuser or /newaquarium is sent, then the user is new to the sistem, so all initialization process start
            self.bot.sendMessage(chat_ID, text = "Welcome! If you want to connect to an alrealdy existing aquarium, write /newuser plus aquarium number if you want to connect a new aquarium you must write /newaquarium")
        elif(self.check_ID(chat_ID) == None and message.startswith(newuser_command)):
            # If the chat_ID is not found and the user types /newuser{int}, then the {int} aquarium is searched in the catalog 
            if self.addnewuser(chat_ID, message[len(newuser_command):]) == False:
                # If aquarium not found, return error
                self.bot.sendMessage(chat_ID, text = "Sorry! This aquarium is not in list check your spelling or add a new aquarium.")
            else:
                # If aquarium found, the user is added to the userList of the {int} aquarium
                self.bot.sendMessage(chat_ID, text = "Congratulations! Now you are in the aquarium list!")
        elif(self.check_ID(chat_ID) == None and message.startswith(newaquarium_command)):
            # If the chat_ID is not found and the user types /newaquarium, then the aquarium is added to the catalog
            self.bot.sendMessage(chat_ID, text = f"Congratulations! Your aquarium number is {self.addnewaquarium(chat_ID)}.")
        else:
            # If the chat_ID is found in the catalog, the aquarium is searched
            aquarium_code = str(self.check_ID(chat_ID))
            
            if self.client: 
                if (self.first_connection[str(aquarium_code)] == True and self.is_feed_time_set[str(aquarium_code)] == False and self.is_cyclicalschedule_set[str(aquarium_code)] == False):
                    # If the client is connected and the aquarium is connected for the first time, then the BOT asks to provide the feeding time
                    self.first_connection[str(aquarium_code)] = False
                    self.bot.sendMessage(chat_ID, text = "At what time do you want to feed the animal? (format HH:MM): ")
                    print(aquarium_code)
                    print(self.first_connection)
                elif(self.first_connection[str(aquarium_code)] == False and self.is_feed_time_set[aquarium_code] == False and self.is_cyclicalschedule_set[aquarium_code] == False):
                    # If the client is connected and the aquarium was already connected, but no feeding time is initialized, then the feeding time is retreived from the aswer to the previous question
                    try:
                        self.feeding_time[str(aquarium_code)] = str(datetime.datetime.strptime(message, '%H:%M').time())[:-3]
                        print(f"FEEDING BOT The feed time set is {self.feeding_time}")
                        self.bot.sendMessage(chat_ID, text = "Feeding time successfully set!")
                        self.is_feed_time_set[aquarium_code] = True                       
                    except ValueError:
                        self.bot.sendMessage(chat_ID, text = "Time format not valid. Please, insert the time using the format HH:MM.")
                    if(self.is_feed_time_set[aquarium_code] == True):
                        # If the feeding time is set, but no cyclical schedule is set, the BOT asks to provide a schedule
                        self.bot.sendMessage(chat_ID, text = "Set the cyclical schedule of the notification (as integer minutes).")
                elif(self.first_connection[aquarium_code] == False and self.is_feed_time_set[aquarium_code] == True and self.is_cyclicalschedule_set[aquarium_code] == False):
                    # If the client is connected and the aquarium was already connected, but no cyclical schedule is initialized, then the schedule is retreived from the aswer to the previous question
                    try:
                        self.notification_schedule[str(aquarium_code)] = int(message)
                        self.bot.sendMessage(chat_ID, text = "Feeding settings successfully completed!")
                        self.is_cyclicalschedule_set[aquarium_code] = True
                    except ValueError:
                        self.bot.sendMessage(chat_ID, text = "Format not valid. Please, insert an integer number of minutes.")
                    if(self.is_cyclicalschedule_set[aquarium_code] == True): 
                        # If the cyclical schedule is initialized, a message is published on the broker with the info in JSON format
                        messageToSend = ({"bn": self.topics[str(aquarium_code)]["topics_feeding"][1], "e": [{"n": "feed", "v": "", "t": None, "u": "bool", "timetable": self.feeding_time[str(aquarium_code)], "cyclical_schedule": int(self.notification_schedule[str(aquarium_code)])}]})
                        self.client.myPublish("IoT/"+str(aquarium_code)+"/telegram/feedsettings", messageToSend)
                        self.feeding.configureaquarium(chat_ID, self.feeding_time[aquarium_code], self.topics[str(aquarium_code)]["topics_feeding"][0], self.topics[str(aquarium_code)]["topics_feeding"][1], self.notification_schedule[aquarium_code], aquarium_code, self.URL)
                elif message == "/light":
                    # User asks for light status 
                    msglight = self.light.on_chat_message(int(aquarium_code))
                    self.bot.sendMessage(chat_ID, text = msglight)
                elif message == "/waterlevel":
                    # User asks for water level status
                    self.bot.sendMessage(chat_ID,text = self.waterlevel.on_chat_message(int(aquarium_code)))
                elif message == "/temperature":
                    # User asks for temperature status
                    self.bot.sendMessage(chat_ID,text = self.temperature.on_chat_message(int(aquarium_code)))
                elif message == "/feed":
                    # User asks for feed status
                    self.bot.sendMessage(chat_ID,text = self.feeding.on_chat_message(int(aquarium_code)))
                elif message == "/graphs":
                    # User asks for plots from thingspeak
                    self.bot.sendMessage(chat_ID,text = self.thingspeak.on_chat_message(int(aquarium_code)))
                elif message == "/statistics":
                    # User asks for statistical analysis
                    buttons = [[InlineKeyboardButton(text = f'LIGHT 💡', callback_data = f'light'), 
                                InlineKeyboardButton(text = f'TEMPERATURE 🌡', callback_data = f'temperature'),
                                InlineKeyboardButton(text = f'WATER LEVEL 🌊', callback_data = f'waterlevel')]]
                    keyboard = InlineKeyboardMarkup(inline_keyboard = buttons)
                    self.bot.sendMessage(chat_ID, text = 'Which statistics do you want to see?', reply_markup = keyboard)
                elif message.isdigit() and self.request[chat_ID]["bool"]:
                    # User already asked for statstical analysis, now it asks for x days of statistical analysis
                    days = int(message)
                    msg = {"days": days, "type": self.request[chat_ID]["type"], "aquarium_code": aquarium_code}
                    self.client.myPublish(self.topics[aquarium_code]["topic_statistics"][self.request[chat_ID]["type"]], msg)
                    self.bot.sendMessage(chat_ID, text = f"Requested statistics of aquarium {aquarium_code} for {days} days.")
                else:
                    self.bot.sendMessage(chat_ID, text = "Sorry! Command not supported!")
            else:
                # Client is not connected
                print("TELEGRAM BOT MQTT client is not connected.")

    def on_callback_query(self, msg):
        query_id, chat_ID, query_data = telepot.glance(msg, flavor = 'callback_query')
        chat_id = msg['message']['chat']['id']
        self.request[chat_id] = {}

        for i in self.chatID.keys():
            for j in self.chatID[i]:
                if j == chat_id:
                    aquariumNumber = i

        if query_data == 'light':
            self.request_days_input(chat_id, 'light')
            self.request[chat_id]["bool"] = True
            self.request[chat_id]["type"] = "light"
            self.request[chat_id]["aquariumID"] = aquariumNumber
        elif query_data == 'temperature':
            self.request_days_input(chat_id, 'temperature')
            self.request[chat_id]["bool"] = True
            self.request[chat_id]["type"] = "temperature"
            self.request[chat_id]["aquariumID"] = aquariumNumber
        elif query_data == 'waterlevel':
            self.request_days_input(chat_id, 'waterlevel')
            self.request[chat_id]["bool"] = True
            self.request[chat_id]["type"] = "waterlevel"
            self.request[chat_id]["aquariumID"] = aquariumNumber
        else:
            self.bot.sendMessage(chat_id, text = "Sorry! Invalid option!")
    
    def request_days_input(self, chat_id, control_type):
        message_to_send = f"Please, enter the number of days for {control_type} statistics.\nYou can type the number directly. Example: 7"
        self.bot.sendMessage(chat_id, text = message_to_send)

    def notify(self, topics, payload):
        print(f"TELEGRAM BOT Notifying on topic {topics} with payload {payload}")
        self.set = json.loads(payload)
        msg = None

        aquarium_code = topics.split("/")[1]

        if topics == self.topics[aquarium_code]["topic_light"]:
            msg = self.light.notify(self.set, aquarium_code)
        elif topics == self.topics[aquarium_code]["topic_waterlevel"]:
            msg = self.waterlevel.notify(self.set, aquarium_code)
        elif topics == self.topics[aquarium_code]["topic_temperature"]:
            msg = self.temperature.notify(self.set, aquarium_code)
        elif topics == self.topics[aquarium_code]["topics_feeding"][0] and self.is_cyclicalschedule_set[aquarium_code] == True:
            msg = self.feeding.notify(self.set, aquarium_code)  
        elif topics == self.topics[aquarium_code]["topic_statistics"]["subscriber"]:
            msg = "The maximum was "+str(self.set["maximum values"])+ "\nThe minimum was "+ str(self.set["minimum values"])+"\nThe average was "+str(self.set["average"])
            for i in self.request.keys():
                if self.request[i]["aquariumID"] == aquarium_code:
                    chat_id = i
            self.bot.sendMessage(chat_id, msg)
            if self.request[chat_id]["type"] == "light":
                self.bot.sendMessage(chat_id, text = "\nThe cost is"+str(self.set["average cost"]))
            self.request[chat_id] = {}

        if msg != None and self.chatID != None and topics != self.topics[aquarium_code]["topic_statistics"]["subscriber"]:
            for i in self.chatID[str(aquarium_code)]:
                self.bot.sendMessage(i, text = msg )

    def subscription_setup(self, topics, broker, port):

        for i in (topics.keys()):
            self.client.mySubscribe(topics[i]["topic_waterlevel"])
            self.client.mySubscribe(topics[i]["topic_light"])
            self.client.mySubscribe(topics[i]["topic_temperature"])
            self.client.mySubscribe(topics[i]["topic_statistics"]["subscriber"])
            self.client.mySubscribe(topics[i]["topics_feeding"][0])
    
    def check_ID(self, chat_ID):
        catalog = requests.get(self.URL+"/service").json()
        ID_users = catalog["usersList"]
        
        for i in ID_users.keys():
            if chat_ID == ID_users[i]["chatID"]:
                return ID_users[i]["aquariums"][0]
        
        return None
    
    def addnewuser(self, chatID, aquarium_number):
        catalog = requests.get(self.URL+"/service").json()
        ID_aquarium = catalog["aquariumList"]
        ID_users = catalog["usersList"]
        added = False

        for i in ID_aquarium.keys():

            if ID_aquarium[i]["aquariumID"]==int(aquarium_number):
                ID_aquarium[i]["chatID"].append(chatID)
                added=True
                
        self.chatID[aquarium_number].append(chatID)
        index=(len(ID_users.keys())+1)
        
        # Add aquarium to catalog
        requests.delete(f"{self.CATALOG_URL}/aquarium/"+str(aquarium_number))
        requests.post(f"{self.CATALOG_URL}/aquarium", json = ID_aquarium[aquarium_number])
        
        # Add user to catalog
        ID_users={"userID":index,"chatID":chatID,"aquariums":[aquarium_number]}
        requests.post(f"{self.CATALOG_URL}/user",json=ID_users)
        catalog = requests.get(f"{self.CATALOG_URL}/service").json()

        if added==False:
            return False
        else:
            return True
        
    def addnewaquarium(self,chatID):
        catalog = requests.get(self.URL+"/service").json()
        ID_aquarium = catalog["aquariumList"]
        ID_users = catalog["usersList"]
        ID_controllers = catalog["controllersList"]
        user_index = len(ID_users.keys())+1
        controller_index = len(ID_controllers.keys())+1
        aquarium_code = str(len(ID_aquarium.keys())+1)
        ID_new_user = {"userID": user_index, "chatID": chatID, "aquariums": [aquarium_code]}

        # Add light control to catalog
        topic_light = "IoT/"+aquarium_code+"/telegram/light"
        new_controller = {"controllerID": controller_index, "aquariumID": int(aquarium_code), "name": "LightSwitch", "topics": [{"topic": "IoT/"+aquarium_code+"/sensors/lightsensor", "type": "Subscriber"}, {"topic": topic_light, "type": "Publisher"}, {"topic": "IoT/"+aquarium_code+"/control/light", "type": "Publisher"}]}
        requests.post(self.URL+"/controller", json = new_controller)

        # Add temperature control to catalog
        controller_index += 1
        topic_temperature = "IoT/"+aquarium_code+"/telegram/temperature"
        new_controller = {"controllerID": controller_index , "aquariumID": int(aquarium_code), "name": "Heater", "topics": [{"topic": "IoT/"+aquarium_code+"/sensors/temperature", "type": "Subscriber"}, {"topic": topic_temperature, "type": "Publisher"}, {"topic": "IoT/"+aquarium_code+"/sensors/heater", "type": "Publisher"}]}
        requests.post(self.URL+"/controller", json = new_controller)
        
        # Add feeding control to catalog
        controller_index += 1
        topic_feed = ["IoT/"+aquarium_code+"/control/feeding", "IoT/"+aquarium_code+"/telegram/feedsettings"]
        new_controller = {"controllerID": controller_index, "aquariumID": int(aquarium_code), "name": "FeedingControl", "topics": [{"topic": "IoT/"+aquarium_code+"/control/feeding", "type": "Publisher"}, {"topic": topic_feed[1], "type": "Subscriber"}, {"topic": "IoT/"+aquarium_code+"/sensors/button", "type": "Subscriber"}]}
        requests.post(self.URL+"/controller", json = new_controller)

        # Add water level control to catalog
        controller_index += 1
        topic_waterlevel = "IoT/"+aquarium_code+"/telegram/waterlevel"
        new_controller = {"controllerID": controller_index, "aquariumID": int(aquarium_code), "name": "WaterLevelControl", "topics": [{"topic": "IoT/"+aquarium_code+"/sensors/waterlevel", "type": "Subscriber"}, {"topic": topic_waterlevel, "type": "Publisher"}]}
        requests.post(f"{self.CATALOG_URL}/controller",json=new_controller)
        
        # Add statistic control to catalog
        controller_index += 1
        topic_statistics = {"temperature": "IoT/"+str(aquarium_code)+"/statistics/temperature", "waterlevel": "IoT/"+str(aquarium_code)+"/statistics/waterlevel", "light": "IoT/"+str(aquarium_code)+"/statistics/light", "subscriber": "IoT/"+str(aquarium_code)+"/telegram/statistics"}
        new_controller = {"controllerID": controller_index ,"aquariumID": int(aquarium_code), "name": "StatisticalControl", "topics": [{"topic": "IoT/"+aquarium_code+"/telegram/statistics", "type": "Publisher"}, {"topic": "IoT/"+str(aquarium_code)+"/statistics", "type": "Subscriber"}]}
        requests.post(f"{self.CATALOG_URL}/controller",json=new_controller)

        # Add aquarium and user to catalog
        topics = {str(aquarium_code): {"topic_temperature": topic_temperature, "topic_waterlevel": topic_waterlevel, "topic_light": topic_light, "topics_feeding": topic_feed, "topic_statistics": topic_statistics}}
        self.topics[str(aquarium_code)] = topics[aquarium_code]
        ID_aquarium = {"aquariumID": int(aquarium_code), "devices": [1,2,3,4], "chatID": [chatID], "feedTime": 0, "feedSchedule": "12:00", "changed": False}
        self.subscription_setup(topics, broker, port)
        requests.post(f"{self.CATALOG_URL}/aquarium", json = ID_aquarium)
        requests.post(f"{self.CATALOG_URL}/user", json = ID_new_user)
        
        self.setupvariables()
        self.client.myPublish(self.topicadd, aquarium_code)
   
        return aquarium_code

    def setupvariables(self):
        catalog = requests.get(self.URL+"/service").json()
        ID_users = catalog["usersList"]
        self.is_feed_time_set = {}
        self.is_cyclicalschedule_set = {}
        self.first_connection = {}
        self.feeding_time = {}
        self.notification_schedule = {}

        aquariumlist = catalog["aquariumList"]
        controllersList = catalog["controllersList"]
        self.topicadd = catalog["topicAdd"]
        self.aquarium_number = len(catalog["aquariumList"].keys())
        
        for i in range(1, self.aquarium_number+1):
            self.chatID[str(i)] = aquariumlist[str(i)]["chatID"]
            if aquariumlist[str(i)]["changed"] == False:
                self.is_feed_time_set[str(i)] = False
                self.is_cyclicalschedule_set[str(i)] = False
                self.first_connection[str(i)] = True
            else:
                self.is_feed_time_set[str(i)] = True
                self.is_cyclicalschedule_set[str(i)] = True
                self.first_connection[str(i)] = False
                self.feeding_time[str(i)] = aquariumlist[str(i)]["feedTime"]
                self.notification_schedule[str(i)] = aquariumlist[str(i)]["feedSchedule"]


if __name__ == "__main__":
    conf = json.load(open("settings.json"))
    token = conf["telegramToken"]

    broker = conf["brokerIP"]
    aquarium_code = 1
    port = conf["brokerPort"]
    topic = conf["mqttTopic"]
    topic_waterlevel = "IoT/1/telegram/waterlevel"
    topic_light = "IoT/1/telegram/light"
    topic_feed = ["IoT/1/control/feeding","IoT/1/telegram/feedingsettings"]
    topic_statistics = {"temperature": "IoT/"+str(aquarium_code)+"/statistics/temperature",
                        "waterlevel": "IoT/"+str(aquarium_code)+"/statistics/waterlevel",
                        "light":"IoT/"+str(aquarium_code)+"/statistics/light",
                        "subscriber": "IoT/"+str(aquarium_code)+"/telegram/statistics"}
    
    topic_temperature = "IoT/1/telegram/temperature"
    
    topics = {str(aquarium_code): {"topic_temperature": topic_temperature, 
                                   "topic_waterlevel": topic_waterlevel, 
                                   "topic_light": topic_light, 
                                   "topics_feeding": topic_feed, 
                                   "topic_statistics": topic_statistics}}

    wlcb = TelegramChatBot(token, broker, port, topics, aquarium_code)

    while True:
        time.sleep(3)
