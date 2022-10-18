#!/usr/bin/python3
from flask import Flask, render_template
import paho.mqtt.client as mqtt


app = Flask(__name__)

topic = 'Nivel_agua/tambo'
topic2 = 'flask'
port = 5000

def on_connect(client, userdata, rc,properties=None):
    client.subscribe(topic)
    client.publish(topic2, "STARTING SERVER")
    client.publish(topic2, "CONNECTED")



def on_message(client, userdata, msg):
    client.publish(topic2,  str(msg.payload.decode("utf-8")))


@app.route('/')
def hello_world():
    return render_template("index.html")

if __name__ == '__main__':
    client = mqtt.Client()
    #client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect('localhost')
    client.loop_start()

    app.run(host='0.0.0.0', port=port)
