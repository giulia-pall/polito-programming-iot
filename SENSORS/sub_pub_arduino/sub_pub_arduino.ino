#include "secrets.h"
#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <utility/wifi_drv.h>
#include <ArduinoJson.h>
#include <string.h>
#define LED_PIN 8

WiFiClient  wifi;
int status = WL_IDLE_STATUS;

PubSubClient client(wifi);

unsigned long t1, dt;
int stato = 0;

void setup() {
  
  WiFiDrv::pinMode(A1, INPUT); //define analog input for water level sensor
  WiFiDrv::pinMode(A0, INPUT); //define analog input for light sensor
  pinMode(LED_PIN, OUTPUT);


  while (!Serial) {
    ;
  }
  Serial.begin(9600);
  Serial.println("Scheda in esecuzione!");

  Serial.print("Connessione...");
  while (status != WL_CONNECTED) {
    status = WiFi.begin(WIFI_SSID, WIFI_PASS);
    Serial.print(".");
    delay(1000);
  }
  Serial.println("\nConnected to WiFi!");

  client.setServer("mqtt.eclipseprojects.io", 1883);
  client.setCallback(callback);

  if (client.connect("ArduinoPub12")) {
    Serial.println("mqtt connected");
    client.subscribe("IoT/1/sensors/heater");
  } else {
    Serial.println("mqtt not connected");
    Serial.print("failed, rc =");
    Serial.println(client.state());
  }

}

void loop() {

  client.loop();
  static int t1=0;
  static int t2=0;
  int  dt_wl = millis() - t1; //time from last measurement of waterlevel
  int dt_ls=millis()-t2;//time from last measurement of lightsensor
  if (dt_wl > 5000) {
    StaticJsonDocument<200> jsonwaterlevel;
    StaticJsonDocument<200> jsonBuffer;
    int unix_timestamp=WiFi.getTime();
    StaticJsonDocument<200> doc;
    JsonArray arrays = doc.to<JsonArray>();
    
    jsonwaterlevel["bn"]="IoT/1/sensors/waterlevel";
    jsonBuffer["n"]="water level";
    jsonBuffer["u"]="Volt";
    jsonBuffer["t"]=unix_timestamp;
    
    int water_value=analogRead(A1);
    jsonBuffer["v"]=water_value;
    char bufferarray [250];
    arrays.add(jsonBuffer);
    jsonwaterlevel["e"]=arrays;
    char mqttbuffer[200];
    serializeJson (jsonwaterlevel,mqttbuffer);
    client.publish(jsonwaterlevel["bn"],mqttbuffer);
    Serial.println("Published waterlevel");
    t1 = millis();
  }
  if (dt_ls>5000){
    StaticJsonDocument<200> jsonlightsensor;
    StaticJsonDocument<200> jsonBuffer;
    int unix_timestamp=WiFi.getTime();
    StaticJsonDocument<200> doc;
    JsonArray arrays = doc.to<JsonArray>();  
    jsonlightsensor["bn"]="IoT/1/sensors/lightsensor";
    jsonBuffer["n"]="light sensor";
    jsonBuffer["u"]="Volt";
    jsonBuffer["t"]=unix_timestamp;
    int light_value=analogRead(A0);
    jsonBuffer["v"]=light_value;
    char bufferarray [250];
    arrays.add(jsonBuffer);
    jsonlightsensor["e"]=arrays;
    char mqttbuffer[200];
    serializeJson (jsonlightsensor,mqttbuffer);
    client.publish(jsonlightsensor["bn"],mqttbuffer);
    Serial.println("Published light");
    t2 = millis();
  }
  
  
}

void callback(char* topic, byte* payload, unsigned int length) {

  String msg;
  StaticJsonDocument<256> doc;

  for (int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  deserializeJson(doc, msg);


  auto status = doc["status"].as<const char*>();
  

  Serial.print("messaggio ricevuto dal topic: ");
  Serial.println(topic);
  Serial.print("Contenuto messaggio: ");
  Serial.println(msg);
  Serial.print("Contenuto estratto dal formato json: ");
  
  Serial.println(status[1]);
  if (strcmp(topic, "IoT/1/sensors/heater") == 0) {

    Serial.println("Topic giusto");
    int value=int(msg[msg.length() - 4])-'0';
    Serial.println(value);
    
  
    


    if (value==0)
    {
      digitalWrite(LED_PIN, LOW);
      Serial.println(value);
    }
      


        
    else
      digitalWrite(LED_PIN,HIGH);

    
    
  }
}
