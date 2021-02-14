#!/usr/bin/python

# Hard-coded python script for sending commands to the Brel Home hub through UDP
# 
# Add at least 1 arguments for position and/or angle
# --position -p, --angle -a
# Example: python /domoticz/scripts/brel.py -p 80 -a 90

import socket, json, argparse
from datetime import datetime

# Config
DEBUG = False # BOOL
HOST = '0.0.0.0' # STRING, IP of hub
PORT = 32100 # INT, port of hub
ACCESSTOKEN = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' # STRING, 32 chars, CAPS
DEVICES = ['f008d17a04d00006', 'f008d17a04d00007'] # DICT containing STRING(s), the devices (blinds) to be controlled

# Parse the arguments
def position_type(astr, min=0, max=100):
	value = int(astr)
	if min<= value <= max:
		return value
	else:
		raise argparse.ArgumentTypeError('Value not in range %s-%s'%(min,max))

def angle_type(astr, min=0, max=180):
	value = int(astr)
	if min<= value <= max:
		return value
	else:
		raise argparse.ArgumentTypeError('Value not in range %s-%s'%(min,max))

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--position', type=position_type, metavar="[0-100]", help='Position percentage (0-100)')
parser.add_argument('-a', '--angle', type=angle_type, metavar="[0-180]", help='Angle degrees (0-180)')
args = parser.parse_args()

if not (args.position or args.angle) is not None:
	parser.error('No action requested, add --position and/or --angle')

TIMESTAMP = str( int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000) )
JSON = {}
JSON_DATA = {}
JSON ['msgType'] = 'WriteDevice'
JSON ['deviceType'] = '10000000'
JSON ['AccessToken'] = ACCESSTOKEN

if args.position is not None:
	JSON_DATA ['targetPosition'] = args.position

if args.angle is not None:
	JSON_DATA ['targetAngle'] = args.angle

JSON ['data'] = JSON_DATA

# Socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.bind(('', PORT))
except:
    if DEBUG:
    	print 'failure to bind'

    s.close()
    raise
    s.setblocking(0)

# Sending
count = 1
for device in DEVICES:
	data = ''
	try:
		if DEBUG:
			print 'Message ' + str(count)

		JSON ['mac'] = str(device)
		JSON ['msgID'] = TIMESTAMP + str(count)

		if DEBUG:
			print json.dumps(JSON)

		s.sendto(bytes(json.dumps(JSON)), (HOST, PORT))
		s.settimeout(2)

		if DEBUG:
			data, addr = s.recvfrom(1024)
			print 'Reply: ' + str(count)
			print data
			
		count = count + 1

	except socket.timeout:
		s.close() # must close socket
		print 'Closing, exception encountered during select' # warn
		raise SystemExit # and quit

s.close() # must close socket
if DEBUG:
	print 'Normal termination. Bye!'
