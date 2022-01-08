from socket import *
import paho.mqtt.client as mqtt
from datetime import datetime

from syslogmp import parse

import os
import argparse
import uuid

version = '1.0.2'

parser = argparse.ArgumentParser()
parser.add_argument('-b', "--mqtt_broker", help="mqtt Broker IP.")
parser.add_argument('-m', "--mqtt_port", help="mqtt port.", type=int, default=1883)
parser.add_argument('-i', "--mqtt_id", help="mqtt id.", default="syslog_to_mqtt_"+hex(uuid.getnode()))
parser.add_argument('-u', "--mqtt_username", help="mqtt username.")
parser.add_argument('-p', "--mqtt_password", help="mqtt password.")
parser.add_argument('-t', "--mqtt_topic", help="mqtt prefix topic.", default="syslog")
parser.add_argument('-l', "--listening_port", help="listening port.", type=int, default=514)
parser.add_argument('-v', "--verbose", help="verbose mode.",action="store_true")
args = parser.parse_args()

print(args)

#quit()

if not (args.mqtt_broker):
    print("retrieving parameters from env...")
    args.mqtt_broker = os.environ['MQTT_BROKER']
    args.mqtt_port = int(os.environ['MQTT_PORT'])
    #args.mqtt_id = os.environ['MQTT_CLIENTID']
    args.mqtt_username = os.environ['MQTT_USERNAME']
    args.mqtt_password = os.environ['MQTT_PASSWORD']
    args.mqtt_topic = os.environ['MQTT_PREFIX']
    try:
        args.verbose = int(os.environ['VERBOSE'])
    except:
        pass

starting = True

def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("Connected to",args.mqtt_broker, flush=True)
        client.connected_flag = True

        now = datetime.now()
        mqttclient.publish(args.mqtt_topic+'/syslog_to_mqtt/informational/internal',now.strftime("%m/%d/%Y %H:%M:%S")+' - connected')
        if starting:
            mqttclient.publish(args.mqtt_topic+'/syslog_to_mqtt/informational/internal',now.strftime("%m/%d/%Y %H:%M:%S")+' - starting up; version=\''+version+'\'')

    else:
        print("Bad connection returned code",rc, flush=True)
        client.connected_flag = False

def on_disconnect(client, userdata, rc):
    print("### disconnecting reason {}".format(str(rc)), flush=True)
    client.connected_flag = False
    #quit()

print('Connecting to',args.mqtt_broker)

mqtt.Client.connected_flag = False
mqttclient = mqtt.Client(args.mqtt_id)
mqttclient.username_pw_set(username=args.mqtt_username, password=args.mqtt_password)
mqttclient.on_connect = on_connect
mqttclient.on_disconnect = on_disconnect
mqttclient.loop_start()
mqttclient.connect(args.mqtt_broker,args.mqtt_port)

#Syslog Parameters
server = "0.0.0.0"  # IP of server listener. 0.0.0.0 for any
#port = 514
buf = 8192*4
#addr = (server,port)
addr = (server,args.listening_port)

#Open Syslog Socket
print('Opening syslog socket: %s/%s' % (server,args.listening_port), flush=True)
TCPSock = socket(AF_INET,SOCK_DGRAM)
TCPSock.bind(addr)
TCPSock.settimeout(2)
if TCPSock.bind:
    print('Opened syslog socket: %s/%s' % (server,args.listening_port), flush=True)

while 1:
    if not mqttclient.connected_flag:
        print("trying to reconnect to",args.mqtt_broker, flush=True)
        try:
            mqttclient.reconnect()
        except:
            print('unable to reconnect...', flush=True)
    try:
        data,addr = TCPSock.recvfrom(buf)
        if args.verbose:
            print("new data:",data)
        #data,addr = TCPSock.recvfrom(1024)
        if not data:
            print ("No response from systems!", flush=True)
            break
        else:
            try:
                message = parse(data)
                if args.verbose:
                    print(message, flush=True)

                mqttclient.publish(args.mqtt_topic+'/'+message.hostname+'/'+str(message.severity).split('.')[1]+'/'+str(message.facility).split('.')[1],message.timestamp.strftime("%m/%d/%Y %H:%M:%S")+' - '+str(message.message.decode('utf-8')).rstrip('\x00').rstrip("\n"))
            except:
                print("Error while parsing message",data, flush=True)
    except:
        #print("timeout")
        pass

TCPSock.close()
