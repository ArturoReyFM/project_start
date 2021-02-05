#include <Arduino.h>

#include <PubSubClient.h>
#include <WiFiManager.h>
#define trigP 5 //D1   conexiones en los pines
#define echoP 4 //D2   conexiones en los pines 
#define alturaMaxima 84.5 
//#define alturaMaxTinaco1 125 cm
#define aguaMin 74.5
#define aguaMax 20
const char * ssid="IZZI-C445";
const char * password = "F82DC011C445";
const char * mqttserver = "192.168.0.6";
const int mqttPort = 1883;   //puerto mosquito este es por defaul


int nivelActual;
int hMax;
int hMin;
long duration;
int nivel;
String espip = "";
bool bombaActivada = false;
bool tamboReady = false;
WiFiClient clienteTinaco;
PubSubClient client(clienteTinaco); 

String IpAddress2String(const IPAddress& ipAddress)
{
  return String(ipAddress[0]) + String(".") +\
  String(ipAddress[1]) + String(".") +\
  String(ipAddress[2]) + String(".") +\
  String(ipAddress[3])  ; 
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.println("Mensaje recibido::::::");
  if((char)payload[0] == '1'){
    Serial.println("Tambo listo para subir agua");
    client.publish("status","Tambo listo para subir agua");
    tamboReady = true;
  }
  else if ((char)payload[0] == '0')
  {
    Serial.println("Tambo necesita agua");
    client.publish("status","Tambo necesita agua");
    tamboReady = false;
  }
  
  
  Serial.println();
  Serial.println("-----------------------");
 
} 

void setup() {
    // put your setup code here, to run once:

  Serial.begin(9600);
  pinMode(trigP,OUTPUT);
  pinMode(echoP,INPUT);
  Serial.println("Pines listos papss");

  hMin = alturaMaxima - aguaMin; // 10cm
  hMax = alturaMaxima - aguaMax; // 80cm

  WiFi.begin(ssid,password);


  while (WiFi.status() != WL_CONNECTED )
  {
    delay(500);
    Serial.println("Conectandose a WiFi... ...");

  }
  Serial.println("Conectado a al red Wifi... :D ....");
  client.setServer(mqttserver,mqttPort);
  client.setCallback(callback);
  while (!client.connected() )
  {
    Serial.println("conectandose a servidor mosquitto");
    if (client.connect("esp8266tinacoArriba"))
    {
      Serial.println("Conectado ... :D....");
      //Serial.println(WiFi.localIP());
      espip = WiFi.localIP().toString();
      Serial.println(espip);
      client.publish("status", "Esp8266_controlador_de_bomba_reconectado"); //Topic name
      client.publish("ips/tinaco", (char*) espip.c_str());
    }
    else
    {
      Serial.print("Fallo conexión ");
      Serial.print(client.state());
      delay(2000);
    }
  }
  client.publish("status","controlador_Tinco_de_arriba_Conectado");
  client.subscribe("status/tambo");
}
// Funcion de reconeccion
void reconnect(){
    //Loop until we connect
    while (!client.connected() )
  {
    Serial.println("conectandose a servidor mosquitto");
    if (client.connect("esp8266tinacoArriba"))
    {
      Serial.println("Conectado ... :D....");
      Serial.println(WiFi.localIP());
      espip = WiFi.localIP().toString();
      client.publish("status", "Esp8266_controlador_de_bomba_reconectado"); //Topic name
      client.publish("ips/tinaco", (char*) espip.c_str());
      client.publish("status","controlador_Tinco_de_arriba_Conectado");
      client.subscribe("status/tambo");
    }
    else
    {
      Serial.print("Fallo conexión ");
      Serial.print(client.state());
      delay(2000);
    }
  }
  client.subscribe("status/tambo");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  // put your main code here, to run repeatedly:
//Para correr que el sistema siempre este conectado a Internet
client.loop();

espip = WiFi.localIP().toString();
    
client.publish("ips/tinaco", (char*) espip.c_str());
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
client.publish("Nivel_agua/tinaco",buffer);


//Condiciones de operacion

if (nivelActual>=hMax && bombaActivada)
{
  Serial.println("Apagar bomba");
  client.publish("Bomba","0"); // Para que apague la bomba el switch
  bombaActivada = false; // Variable de control

}
else if (nivelActual<=hMin  && !bombaActivada && tamboReady)
{
  client.publish("Bomba","1"); // Para que prenda la bomba el relevador.
  bombaActivada = true;
  Serial.println("Prender la bomba");
}
else if (bombaActivada && !tamboReady){
  Serial.println("Apagar bomba");
  client.publish("Bomba","0"); // Para que apague la bomba el switch
  bombaActivada = false; // Variable de control

}
else if (tamboReady && nivelActual<hMax && nivelActual > hMin){
  client.publish("Bomba","1"); // Para que prenda la bomba el relevador.
  bombaActivada = true;
  Serial.println("Prender la bomba");
}

delay(500);

}

/// 



