#include <Arduino.h>

#include <PubSubClient.h>
#include <WiFiManager.h>
#define trigP 5 //D1
#define echoP 4 //D2
#define alturaMaxima 86
//#define alturaMaxTambo 125 cm
#define aguaMin 71 // distancia del agua minima al sensor
#define aguaMax 10 // distancia del agua máxima al sensor
const char * ssid="IZZI-C445";
const char * password = "F82DC011C445";
const char * mqttserver = "192.168.0.6";
const int mqttPort = 1883;

int nivelActual;
int hMax;
int hMin;
long duration;
int nivel;
WiFiClient clienteTambo;
PubSubClient client(clienteTambo); 




void setup() {
  // put your setup code here, to run once:

Serial.begin(9600);
pinMode(trigP,OUTPUT);
pinMode(echoP,INPUT);
Serial.println("Pines listos para el TAMBO papss");

hMin = alturaMaxima - aguaMin;
hMax = alturaMaxima - aguaMax;

WiFi.begin(ssid,password);

while (WiFi.status() != WL_CONNECTED )
{
  delay(500);
  Serial.println("Conectandose a WiFi... ...");

}
Serial.println("Conectado a al red Wifi... :D ....");
client.setServer(mqttserver,mqttPort);
while (!client.connected() )
{
  Serial.println("conectandose a servidor mosquitto");
  if (client.connect("esp8266tamboAbajo"))
  {
    Serial.println("Conectado ... :D....");
    Serial.println(WiFi.localIP());
  }
  else
  {
    Serial.print("Fallo conexión ");
    Serial.print(client.state());
    delay(2000);
  }

client.publish("status","controlador_Tambo_de_abajo_Conectado");

  
}


}

void loop() {
  // put your main code here, to run repeatedly:
//Para correr que el sistema siempre este conectado a Internet
client.loop();
//Entorno de medida del sistema
digitalWrite(trigP,LOW);
delayMicroseconds(2);
digitalWrite(trigP,HIGH);
delayMicroseconds(10);
digitalWrite(trigP,LOW);

duration = pulseIn(echoP,HIGH);

nivel = duration*0.034/2;
nivelActual = alturaMaxima-nivel;
Serial.print("Nivel de agua actual:");
Serial.print(nivelActual);
Serial.println("cm");
constexpr size_t buffer_size = 10;
char buffer[buffer_size];
dtostrf(nivelActual,buffer_size-1,2,buffer);
buffer[7]='c';
buffer[8]='m';
client.publish("Nivel_agua/tambo",buffer);


//Condiciones de operacion

if (nivelActual >= hMax)
{
  Serial.println("::::::Encender bomba::::::");
  client.publish("status/tambo","1");
}
else if (nivelActual <= hMin)
{
  Serial.println("::::::Apagar bomba::::::");
  client.publish("status/tambo","0");
}

delay(500);

}

/// 