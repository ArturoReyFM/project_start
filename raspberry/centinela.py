import paho.mqtt.client as mqtt
import time as tm
import platform    # For getting the operating system name
import subprocess  # For executing a shell command
from threading import Thread
import logging
import sys

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
    
    return conectado

def on_message(client,userdata,message):
    msg = str(message.payload.decode("utf-8"))
    topico = message.topic.split("/")[0]
    if topico == "Nivel_agua" and '.' in msg :
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

    elif message.topic == "Bomba":
       
        if msg=="1" and stats.bombaActivada == False:
            stats.bombaActivada = True
            stats.temporizador = tm.time() # iniciar temporizador para medir el tiempo de vaciado del tambo
            stats.deltaNivelTambo = stats.nivelTambo # medir nivel inicial
           
        elif msg == "0" and stats.bombaActivada == True:
            stats.bombaActivada = False
            stats.temporizador = tm.time() - stats.temporizador # calcular tiempo transcurrido de vaciado
            stats.deltaNivelTambo = abs(stats.nivelTambo - stats.deltaNivelTambo)
            stats.publicar("[INFO] Se vaciaron {:.2} cm en{:.2f} seg".format(stats.deltaNivelTambo,stats.temporizador),"status")
            #client.publish("status","[INFO] Velocidad aproximada de la bomba {:.2}")

    
     
class ControladorBomba:
    def __init__(self,logger):
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
        self.temporizador = 0.0
        self.deltaNivelTambo = 0.0
        self.notificacion_actual = ""
        self.logger = logger

    
    def set_mqtt_client(self):
        try:
            self.clienteMqtt=mqtt.Client("centinela")
            self.clienteMqtt.connect("localhost")
            self.clienteMqtt.subscribe("Nivel_agua/tinaco")
            self.clienteMqtt.subscribe("Nivel_agua/tambo")
            self.clienteMqtt.subscribe("ips/tambo")
            self.clienteMqtt.subscribe("ips/tinaco")
            self.clienteMqtt.subscribe("status/tambo")
            self.clienteMqtt.subscribe("modo")
            self.clienteMqtt.subscribe("Bomba")
            self.clienteMqtt.publish("status","Centinela activo")
            self.clienteMqtt.on_message=on_message
        except Exception as e:
            logger.critical("Error al conectarse a servidor mqtt",e)

    def operacionTinaco(self,nivelMaxTinaco, nivelMinTinaco):
        
        
        if self.nivelTinaco >= nivelMaxTinaco and self.bombaActivada:
            self.clienteMqtt.publish("Bomba","0")
            
        elif self.nivelTinaco <= nivelMinTinaco and not self.bombaActivada and self.tamboListo:
            self.clienteMqtt.publish("Bomba","1")

        elif self.bombaActivada and not self.tamboListo:
            self.clienteMqtt.publish("Bomba","0")
            
        elif self.tamboListo and nivelMinTinaco < self.nivelTinaco < nivelMaxTinaco:
            self.clienteMqtt.publish("Bomba","1")
        
        elif nivelMinTinaco < self.nivelTinaco < nivelMaxTinaco and not self.tamboListo and not self.bombaActivada:
            tm.sleep(1)
            



    def operacionTambo(self,nivelMaxTambo,nivelMinTambo):
        
        if self.nivelTambo >= nivelMaxTambo:
            self.clienteMqtt.publish("mensajes_tambo","+---\tLISTO PARA SUBIR AGUA\t---+")
            self.notificacion_actual = "LISTO PARA SUBIR AGUA"
            self.tamboListo = True
        elif self.nivelTambo <= nivelMinTambo :
            self.tamboListo = False
            self.clienteMqtt.publish("mensajes_tambo","+---\tSE NECESITA AGUA PARA SUBIR.\t---+")
            self.notificacion_actual = "TAMBO SIN AGUA"
            tm.sleep(1)
        elif self.nivelTambo <= nivelMaxTambo and not self.bombaActivada:
            self.clienteMqtt.publish("mensajes_tambo","+---\tTAMBO NECESITA AGUA\t---+")
            self.notificacion_actual = "TAMBO PARCIALMENTE LLENO."
            tm.sleep(1) 
        elif self.nivelTambo <= nivelMaxTambo and self.bombaActivada:
            self.clienteMqtt.publish("mensajes_bomba","+---\tSUBIENDO AGUA\t---+")
            self.notificacion_actual = "SUBIENDO AGUA"
            tm.sleep(1)
            
            
            
    def operacionSemiAutomatica(self,nivelMaxTambo,nivelMinTambo):
        if self.nivelTambo >= nivelMaxTambo:
            self.publicar("+---\tLISTO PARA SUBIR AGUA. CERRAR  DEL TAMBO\t---+","mensajes_tambo")
            self.notificacion_actual = "CERRAR LA LLAVE DEL AGUA DEL TAMBO, ESTA LLENO"
            self.tamboListo = True
            tm.sleep(1)
        elif self.nivelTambo <= nivelMinTambo:
            self.tamboListo = False
            self.publicar("+---\tNIVEL DE AGUA MUY BAJO\t---+","mensajes_tambo")
            self.notificacion_actual = "TAMBO SIN AGUA" 
            self.clienteMqtt.publish("Bomba","0")
            tm.sleep(1)
        elif self.nivelTambo <= nivelMaxTambo and not self.bombaActivada:
            self.publicar("+---\tTAMBO PUEDE SUBIR AGUA\t---+","mensajes_tambo")
            self.notificacion_actual = "PUEDE SUBIR AGUA DEL TAMBO"
            #self.clienteMqtt.publish("status","[INFO] Nivel del tambo al {:.2f} %".format(self.porciento_llenado("tambo")))
            tm.sleep(1)
        elif self.nivelTambo <= nivelMaxTambo and self.bombaActivada:
            self.clienteMqtt.publish("status","+---LLENANDO TINACO, BOMBA ACTIVADA\t---+")
            self.notificacion_actual = "SUBIENDO AGUA"
            tm.sleep(0.5)

    def porciento_llenado(self,componente):
        if componente == "tambo":
            return (self.nivelTambo * 100)/nivelMaxTambo
        elif  componente == "tinaco":
            return (self.nivelTinaco * 100)/nivelMaxTinaco
    
    def publishStatus(self):
        self.clienteMqtt.publish("nivel_tambo_%","Nivel -> {:2f} %".format(self.porciento_llenado("tambo")))
        self.clienteMqtt.publish("nivel_tinaco_%","Nivel->{:2f} %".format(self.porciento_llenado("tinaco")))
        self.clienteMqtt.publish("status","+\tTambo-{}\tTinaco-{}\t{}".format(self.tambo,self.tinaco,self.modo))
        self.clienteMqtt.publish("status","\t{:.2f} %     \t{:.2f} %".format(self.porciento_llenado("tambo"),self.porciento_llenado("tinaco")))
    def publicar(self,topic="status",mensaje):
        #mensaje = mensaje.upper()
        #mensaje = "+---\t"+mensaje+"\t---+"
        self.clienteMqtt.publish(topic,mensaje)

    def publicar_notificacion_front(self):
        tambo = "Activado" if self.tambo else "Desactivado"
        tinaco = "Activado" if self.tinaco else "Desactivado"
        modo = self.modo
        bomba = "Activada" if self.bombaActivada else "Desactivada"
        mensaje = self.notificacion_actual
        notificacion ="{}-{}-{}-{}-{}".format(tambo,tinaco,bomba,modo,mensaje)
        self.publicar(topic="notificaciones",mensaje=notificacion)

        


def obtener_status_sensores(stats,logger):
    try:
        while True:
            stats.tinaco = ping(stats.ipTinaco)
            stats.tambo = ping(stats.ipTambo)
            tm.sleep(1)
    except Exception as e:
        logger.warning("No se pudo obtener ips {}".format(e))
def ejecutar_centinela(stats,logger):
    while True:
        try:
            stats.publishStatus()
            stats.publicar_notificacion_front()
            if stats.modo == "automatico":
                if stats.tambo:
                    stats.operacionTambo(nivelMaxTambo,nivelMinTambo)
                else:
                    stats.bombaActivada = False
                    stats.publicar("Sin funcionar","mensajes_tambo")
                if stats.tinaco:
                    stats.operacionTinaco(nivelMaxTinaco,nivelMinTinaco)
                else:
                    stats.bombaActivada = False
                    stats.publicar("Sin funcionar","mensajes_tinaco")
                tm.sleep(1)

            elif stats.modo == "semiautomatico":
                stats.operacionSemiAutomatica(nivelMaxTambo,nivelMinTambo)
               
                if not stats.tambo:
                    stats.bombaActivada = False
                    stats.publicar("Sin funcionar","mensajes_tambo")
                if not stats.tinaco:
                    stats.publicar("Sin funcionar","mensajes_tinaco")
                tm.sleep(1)
            elif stats.modo == "manual" :
                if not stats.tambo:
                    stats.publicar("Sin funcionar","mensajes_tambo")
                if not stats.tinaco:
                    stats.publicar("Sin funcionar","mensajes_tinaco")
                stats.notificacion_actual="REVISAR LOS NIVELES DE AGUA CONSTANTEMENTE"
                
                tm.sleep(1)
        except Exception as e:
            logger.error("Error al ejecutar centinela {}".format(e))
            sys.exit(1)

def main(logger):
    
    stats.set_mqtt_client()
    try:
        stats.tinaco = ping(stats.ipTinaco)
        stats.tambo = ping(stats.ipTambo)
    except Exception as errorIp:
        logger.warning("No se pudo obtener ips de sensores")
    try:
        stats.clienteMqtt.loop_start()
    except Exception as e:
        logger.critical("Error al inicial loop mqtt")
        sys.exit(0)
    Tarea1 = Thread(target=ejecutar_centinela,args=(stats,logger))
    Tarea2 = Thread(target=obtener_status_sensores,args=(stats,logger))
    Tarea1.start()
    Tarea2.start()


if __name__=='__main__':
    # create logger
    
    # Create and configure logger
    logging.basicConfig(filename="centinela.log",
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        filemode='w')
    
    # Creating an object
    logger = logging.getLogger()
    
    # Setting the threshold of logger to DEBUG
    logger.setLevel(logging.DEBUG)

    stats = ControladorBomba(logger)
    main(logger)
