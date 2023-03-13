import socket as sock
from socket import *

import paho.mqtt.client as mqtt
from datetime import datetime

import os
import argparse
import uuid

from dataclasses import dataclass

version = '1.2.0'

Facility = ['kernel','user','mail','system_daemons','security4','internal','line_printer','network_news','uucp','clock9','security10','ftp','ntp','log_audit','log_alert','clock15','local0','local1','local2','local3','local4','local5','local6','local7']
Severity = ['emergency','alert','critical','error','warning','notice','info','debug']

@dataclass(frozen=True)
class Message:
    facility: str
    facility_id: int
    severity: str
    severity_id: int
    timestamp: datetime
    hostname: str
    message: str

def pop(data,match=' ',nb=1):
    ptr=0
    while nb:
        i=data[ptr:].index(match)
        ptr=ptr+i+1
        nb-=1
    return (data[0:ptr-1],data[ptr:])

def syslog_3164(data) -> Message:
    data=data.decode("utf-8")
    #print('analyse',data)
    PRI,data = pop(data,'>')
    facility_id, severity_id = divmod(int(PRI[1:]), 8)
    # replace 0 in date if not present for datetime conversion
    if data[4]==' ':
        data=data[:4]+'0'+data[5:]
    logdate,data = pop(data,' ',3)
    host,message = pop(data)
    log_datetime = datetime.strptime(logdate,'%b %d %H:%M:%S')
    log_datetime = log_datetime.replace(year=datetime.now().year)

    return Message(
            facility=Facility[facility_id],
            facility_id=facility_id,
            severity=Severity[severity_id],
            severity_id=severity_id,
            timestamp=log_datetime,
            hostname=host,
            message=message.rstrip('\x00').rstrip("\n"),
        )

parser = argparse.ArgumentParser()
parser.add_argument('-b', "--mqtt_broker", help="mqtt Broker IP.")
parser.add_argument('-m', "--mqtt_port", help="mqtt port.", type=int, default=1883)
parser.add_argument('-i', "--mqtt_id", help="mqtt id.", default="syslog_to_mqtt_"+hex(uuid.getnode()))
parser.add_argument('-u', "--mqtt_username", help="mqtt username.")
parser.add_argument('-p', "--mqtt_password", help="mqtt password.")
parser.add_argument('-t', "--mqtt_topic", help="mqtt prefix topic.", default="test")
parser.add_argument('-s', "--mqtt_tls", help="mqtt use tls.", action="store_true")
parser.add_argument('-l', "--listening_port", help="listening port.", type=int, default=514)
parser.add_argument('-v', "--verbose", help="verbose mode.", action="store_true")
args = parser.parse_args()

if not (args.mqtt_broker):
    print("retrieving parameters from env...")
    args.mqtt_broker = os.environ['MQTT_BROKER']
    args.mqtt_port = int(os.environ['MQTT_PORT'])
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
if args.mqtt_tls:
    import certifi
    mqttclient.tls_set(certifi.where())
mqttclient.on_connect = on_connect
mqttclient.on_disconnect = on_disconnect
mqttclient.loop_start()
mqttclient.connect(args.mqtt_broker,args.mqtt_port)

#Syslog Parameters
server = "0.0.0.0"  # IP of server listener. 0.0.0.0 for any
buf = 8192*4
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
        if not data:
            print ("No response from systems!", flush=True)
            break
        else:
            try:
                message = syslog_3164(data)
                if args.verbose:
                    print(message, flush=True)
            except:
                print("Error while parsing message",data, flush=True)
            try:
                mqttclient.publish(args.mqtt_topic+'/'+message.hostname+'/'+message.severity+'/'+message.facility,message.timestamp.strftime("%m/%d/%Y %H:%M:%S")+' - '+message.message)
            except:
                print("Error while sending to",args.mqtt_broker, flush=True)
    except (TimeoutError, sock.timeout):
        pass

TCPSock.close()