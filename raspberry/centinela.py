import paho.mqtt.client as mqtt
import time as tm
import platform    # For getting the operating system name
import subprocess  # For executing a shell command



alturaMaximaTambo = 86 # Altura máxima desde la base del tambo al sensor
alturaMaximaTinaco = 84.5 # Altura màxima desde la base del tinaco al sensor

# Distancias relativas desde  el sensor de tinaco y tambo al nivel de agua predeterminado 
aguaMinTambo = 71
aguaMaxTambo = 19
aguaMinTinaco = 74.5
aguaMaxTinaco = 20

# Calcular niveles de agua relativas a la base de tinaco y tambo 
nivelMaxTinaco = alturaMaximaTinaco - aguaMaxTinaco
nivelMinTinaco = alturaMaximaTinaco -aguaMinTinaco
nivelMaxTambo = alturaMaximaTambo - aguaMaxTambo
nivelMinTambo = alturaMaximaTambo - aguaMinTambo



def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]
   

    conectado = subprocess.call(command) == 0
    print("\r")
    print("\r")
    print("\r")
    print("\r")
    print("\r")
    print("\r")

    return conectado

def on_message(client,userdata,message):
    msg = str(message.payload.decode("utf-8"))
    
    topico = message.topic.split("/")[0]
    if topico == "Nivel_agua":
        sensor = message.topic.split("/")[1]
        nivel = float(msg.split('.')[0])
        if nivel > -1000 and nivel <= 90 and sensor=="tinaco":
            #print("[INFO] Sensor",sensor,"funcionando correctamente")
            stats.tinaco=True
            stats.nivelTinaco = nivel
        if nivel > -1000 and nivel <= 90 and sensor=="tambo":
            #print("[INFO] Sensor",sensor,"funcionando correctamente")
            stats.tambo=True
            stats.nivelTambo = nivel
    elif topico == "ips":
        if message.topic.split("/")[1]=="tinaco":
            stats.ipTinaco = msg
        else:
            stats.ipTambo = msg

    elif message.topic == "modo":
        if msg == "manual":
            stats.modo = "manual"

        elif msg == "automatico":
            stats.modo = "automatico"

        elif msg == "semiautomatico":
            stats.modo = "semiautomatico"
        else:
            client.publish("modo","Escribe manual o automatico")
        
class status:
    def __init__(self):
        self.tinaco = False
        self.tambo = False
        self.ipTinaco = ""
        self.ipTambo=""
        self.nivelTinaco = 0
        self.nivelTambo = 0
        self.bombaActivada = False
        self.tamboListo = False
        self.clienteMqtt = None
        self.modo = "automatico" ## modo automatico
    
    def set_mqtt_client(self):

        self.clienteMqtt=mqtt.Client("centinela")
        self.clienteMqtt.connect("localhost")
        self.clienteMqtt.subscribe("Nivel_agua/tinaco")
        self.clienteMqtt.subscribe("Nivel_agua/tambo")
        self.clienteMqtt.subscribe("ips/tambo")
        self.clienteMqtt.subscribe("ips/tinaco")
        self.clienteMqtt.subscribe("status/tambo")
        self.clienteMqtt.subscribe("modo")
        self.clienteMqtt.publish("status","Centinela activo")
        self.clienteMqtt.on_message=on_message

    def operacionTinaco(self,nivelMaxTinaco, nivelMinTinaco):
        
        print("Nivel del tinaco:",self.nivelTinaco)
        if self.nivelTinaco >= nivelMaxTinaco and self.bombaActivada:
            print("Apagar bomba")
            self.clienteMqtt.publish("Bomba","0")
            self.bombaActivada = False

        elif self.nivelTinaco <= nivelMinTinaco and not self.bombaActivada and self.tamboListo:
            print("Prender Bomba")
            self.clienteMqtt.publish("Bomba","1")
            self.bombaActivada = True

        elif self.bombaActivada and not self.tamboListo:
            print("Apagar bomba")
            self.clienteMqtt.publish("Bomba","0")
            self.bombaActivada = False

        elif self.tamboListo and nivelMinTinaco < self.nivelTinaco < nivelMaxTinaco:
            print("Prender Bomba")
            self.clienteMqtt.publish("Bomba","1")
            self.bombaActivada = True

    def operacionTambo(self,nivelMaxTambo,nivelMinTambo):

        print("Nivel del tambo:",self.nivelTambo)

        if self.nivelTambo >= nivelMaxTambo:
            print("Tambo listo para subir agua")
            self.clienteMqtt.publish("status","[INFO] TAMBO listo para subir agua")
            self.tamboListo = True

        elif self.nivelTambo <= nivelMinTambo:
            print("Tambo necesita agua")
            self.tamboListo = False
            self.clienteMqtt.publish("status","[INFO] TAMBO NECESITA AGUA")

        elif self.nivelTinaco <= nivelMaxTambo:
            print("Tambo necesita agua")
            self.clienteMqtt.publish("status","[INFO] TAMBO NECESITA AGUA")
            
    def operacionSemiAutomtica(self,nivelMaxTambo,nivelMinTambo):
        print("Nivel del tambo:",self.nivelTambo)

        if self.nivelTambo >= nivelMaxTambo:
            print("Tambo listo para subir agua")
            self.clienteMqtt.publish("status","[INFO] TAMBO listo para subir agua")
            self.tamboListo = True

        elif self.nivelTambo <= nivelMinTambo:
            print("Tambo necesita agua")
            self.tamboListo = False
            self.clienteMqtt.publish("status","[INFO] TAMBO NECESITA AGUA")
            print("Apagar bomba")
            self.clienteMqtt.publish("Bomba","0")
            self.bombaActivada = False

        elif self.nivelTinaco <= nivelMaxTambo:
            print("Tambo necesita agua")
            self.clienteMqtt.publish("status","[INFO] TAMBO NECESITA AGUA")


            

stats = status()

def main():
    stats.set_mqtt_client()

    while True:
        print("Modo:",stats.modo)
        stats.clienteMqtt.loop_start()
        if stats.modo == "automatico":
            
            stats.operacionTambo(nivelMaxTambo,nivelMinTambo)
            stats.operacionTinaco(nivelMaxTinaco,nivelMinTinaco)
            stats.clienteMqtt.publish("status","[INFO] Tambo activado:{} Tinaco activado:{}".format(stats.tambo,stats.tinaco))
            if stats.tambo!=True or stats.tinaco!=True:
                print("[INFO] Se mantiene bomba apagada")
                print("[INFO] Tambo activado:",stats.tambo,"Tinaco activado:",stats.tinaco)
                stats.clienteMqtt.publish("status","[INFO] Tambo activado:{} Tinaco activado:{}".format(stats.tambo,stats.tinaco))
                stats.bombaActivada = False
            stats.tinaco = ping(stats.ipTinaco)
            stats.tambo = ping(stats.ipTambo)

        elif stats.modo == "semiautomatico":

            print("[INFO] El sistema está en modo semiautomatico. Tome sus precauciones. Checar constantemente el nivel de agua.")
            stats.operacionSemiAutomtica(nivelMaxTambo,nivelMinTambo)
            stats.clienteMqtt.publish("status","[INFO] Tambo activado:{}".format(stats.tambo))

            if stats.tambo!=True:
                print("[INFO] Se mantiene bomba apagada")
                print("[INFO] Tambo activado:",stats.tambo,"Tinaco activado:",stats.tinaco)
                stats.clienteMqtt.publish("status","[INFO] Tambo activado:{} Tinaco activado:{}".format(stats.tambo,stats.tinaco))
                stats.bombaActivada = False
            
            stats.tambo = ping(stats.ipTambo)


        elif stats.modo == "manual" :
            print("[INFO] El sistema está en modo manual. Tome sus precauciones. Checar constantemente el nivel de agua.")
            stats.clienteMqtt.publish("status","[INFO] El sistema está en modo manual. Tome sus precauciones. Checar constantemente el nivel de agua.")
            tm.sleep(1)            

        

if __name__=='__main__':
    main()
