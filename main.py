from socket import *
import paho.mqtt.client as mqtt
from datetime import datetime

from syslogmp import parse

import os

version = '1.0.0'

mqttbroker = os.environ['MQTT_BROAKER']
mqttport = int(os.environ['MQTT_PORT'])
mqtt_client_id = os.environ['MQTT_CLIENTID']
mqttusername = os.environ['MQTT_USERNAME']
mqttpassword = os.environ['MQTT_PASSWORD']
mqtt_prefix = os.environ['MQTT_PREFIX']

starting = True

def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("Connected to",mqttbroker, flush=True)
        client.connected_flag = True

        now = datetime.now()
        mqttclient.publish(mqtt_prefix+'/syslog_to_mqtt/informational/internal',now.strftime("%m/%d/%Y %H:%M:%S")+' - connected')
        if starting:
            mqttclient.publish(mqtt_prefix+'/syslog_to_mqtt/informational/internal',now.strftime("%m/%d/%Y %H:%M:%S")+' - starting up; version=\''+version+'\'')

    else:
        print("Bad connection returned code",rc, flush=True)
        client.connected_flag = False

def on_disconnect(client, userdata, rc):
    print("### disconnecting reason {}".format(str(rc)), flush=True)
    client.connected_flag = False
    #quit()

print('Connecting to',mqttbroker)

mqtt.Client.connected_flag = False
mqttclient = mqtt.Client(mqtt_client_id)
mqttclient.username_pw_set(username=mqttusername, password=mqttpassword)
mqttclient.on_connect = on_connect
mqttclient.on_disconnect = on_disconnect
mqttclient.loop_start()
mqttclient.connect(mqttbroker,mqttport)

#Syslog Parameters
server = "0.0.0.0"  # IP of server listener. 0.0.0.0 for any
port = 514
buf = 8192*4
addr = (server,port)

#Open Syslog Socket
print('Opening syslog socket: %s/%s' % (server,port), flush=True)
TCPSock = socket(AF_INET,SOCK_DGRAM)
TCPSock.bind(addr)
TCPSock.settimeout(2)
if TCPSock.bind:
    print('Opened syslog socket: %s/%s' % (server,port), flush=True)

while 1:
    if not mqttclient.connected_flag:
        print("trying to reconnect to",mqttbroker, flush=True)
        try:
            mqttclient.reconnect()
        except:
            print('unable to reconnect...', flush=True)
    try:
        data,addr = TCPSock.recvfrom(buf)
        #data,addr = TCPSock.recvfrom(1024)
        if not data:
            print ("No response from systems!", flush=True)
            break
        else:
            try:
                message = parse(data)
                print(message, flush=True)

                mqttclient.publish(mqtt_prefix+'/'+message.hostname+'/'+str(message.severity).split('.')[1]+'/'+str(message.facility).split('.')[1],message.timestamp.strftime("%m/%d/%Y %H:%M:%S")+' - '+str(message.message.decode('utf-8')).rstrip("\n"))
            except:
                print("Error while parsing message",data, flush=True)
    except:
        #print("timeout")
        pass

TCPSock.close()
