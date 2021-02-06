import paho.mqtt.client as mqtt
import time as tm
import platform    # For getting the operating system name
import subprocess  # For executing a shell command


class status:
    def __init__(self):
        self.tinaco = False
        self.tambo = False
        self.ipTinaco = ""
        self.ipTambo=""

stats = status()

def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    return subprocess.call(command) == 0
def on_message(client,userdata,message):
    msg = str(message.payload.decode("utf-8"))
    nivel = float(msg.split('.')[0])
    sensor = message.topic.split("/")[1]
    if message.topic.split("/")[0]=="Nivel_agua":
        if nivel > -1000 and nivel <= 90 and sensor=="tinaco":
            print("[INFO] Sensor",sensor,"funcionando correctamente")
            stats.tinaco=True
        if nivel > -1000 and nivel <= 90 and sensor=="tambo":
            print("[INFO] Sensor",sensor,"funcionando correctamente")
            stats.tambo=True
    elif message.topic.split("/")[0]=="ips":
        if message.topic.split("/")[1]=="tinaco":
            stats.ipTinaco = msg
        else:
            stats.ipTambo = msg
        
def main():
    client=mqtt.Client("centinela")
    client.connect("localhost")
    client.subscribe("Nivel_agua/tinaco")
    client.subscribe("Nivel_agua/tambo")
    client.subscribe("ips/tambo")
    client.subscribe("ips/tinaco")
    client.publish("status","Centinela activo")
    client.on_message=on_message

    while True:
        client.loop_start()
        if stats.tambo!=True or stats.tinaco!=True:
            print("[INFO] Se mantiene bomba apagada")
            print("[INFO] Tambo activado:",stats.tambo,"Tinaco activado:",stats.tinaco)
            client.publish("status","[INFO] Tambo activado:{} Tinaco activado:{}".format(stats.tambo,stats.tinaco))
            client.publish("Bomba","0")
        stats.tinaco = ping(stats.ipTinaco)
        stats.tambo = ping(stats.ipTambo)
        tm.sleep(2)

if __name__=='__main__':
    main()
