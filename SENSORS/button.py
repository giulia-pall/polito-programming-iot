import RPi.GPIO as GPIO
import time
import paho.mqtt.client as PahoMQTT
import json
import time
from MyMQTT import *
class button:
    def __init__(self,ClientID,broker,topic,pin):
        self.clientID=ClientID
        self.broker=broker
        self.pin=pin
       

        self.client=MyMQTT(self.clientID,self.broker,1883,self)
        self.topic=topic

    def startOperation(self):
        self.client.start()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)
        time.sleep(3)
        
    def setstatus(self):
        try:

            state = GPIO.input(self.pin)
            if state == False:
                msg=({"bn":self.topic,"e": [{"n": "button","v": 1,"t": None, "u": "bool"}]})
                self.client.myPublish(self.topic,msg)
                print("message sent")
            else:
                print("Pulsante rilasciato")
            time.sleep(0.1)  # Aggiungi un piccolo ritardo per evitare letture multiple
        except KeyboardInterrupt:
            GPIO.cleanup()

        
        
        
    



if __name__=="__main__":
    pushbutton=button("Alex99ddffhgcf","mqtt.eclipseprojects.io","IoT/1/sensors/button",27)
    pushbutton.startOperation()
    while(1):
        pushbutton.setstatus()
        time.sleep(1)




















