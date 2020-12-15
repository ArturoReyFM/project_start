#include <Arduino.h>
#include <WiFiManager.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <iostream> 
const char* ssid = "IZZI-C445"; // Enter your WiFi name
//const char* ssid = "INFINITUMA451_2.4"; // Enter your WiFi name
const char* password =  "F82DC011C445"; // Enter WiFi password
//const char* password =  "EswVMseZ7e"; // Enter WiFi password
const char* mqttServer = "192.168.0.6";
//const char* mqttServer = "192.168.1.96";
const int mqttPort = 1883;
const char * espip = "";
#define RELAY 0 // relay connected to  GPIO0
//const char* mqttUser = "otfxknod";
//const char* mqttPassword = "nSuUc1dDLygF";
 
WiFiClient espClient;
PubSubClient client(espClient);
void callback(char* topic, byte* payload, unsigned int length) {
 
  Serial.print("Message arrived in topic: ");
  Serial.println(topic);
 
  Serial.print("Message:");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
  Serial.println("-----------------------");
  int value = LOW;
   //Switch on the LED if an 1 was recieved as first character
    if((char)payload[0] == '1'){
      Serial.println("RELAY=ON");
      client.publish("status","Bomba desactivada");
      digitalWrite(RELAY,LOW);
      value = LOW;
    }
    else if ((char)payload[0] == '0'){
      Serial.println("RELAY=OFF");
      client.publish("status","Bomba activada");
      digitalWrite(RELAY,HIGH);
      value = HIGH;
    }
 
} 


void setup() {
 
  Serial.begin(9600);
  pinMode(RELAY,OUTPUT);
  digitalWrite(RELAY, HIGH);
  WiFi.begin(ssid, password);
 
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to WiFi..");
  }
  Serial.println("Connected to the WiFi network");
 
  client.setServer(mqttServer, mqttPort);
  client.setCallback(callback);
 
  while (!client.connected()) {
    Serial.println("Connecting to MQTT...");
 
    if (client.connect("ESP8266Relay" )) {
 
      Serial.println("connected");
      Serial.println(WiFi.localIP());
      espip = WiFi.localIP().toString().c_str();
    } else {
 
      Serial.print("failed with state ");
      Serial.print(client.state());
      delay(2000);
 
    }
  }
  
  client.publish("status", "Esp8266_controlador_de_bomba_conectado"); //Topic name
  client.publish("status", espip);
  client.subscribe("Bomba");
 
}
 

 
void loop() {
  client.loop();
 
}