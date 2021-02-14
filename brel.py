#!/usr/bin/env python
#v.1.0.0
import Domoticz
import socket, json
from datetime import datetime
import re

class brel:

	JSON = {}

	def __init__(self, host=None, port=None, brel_devices={}):
		self.host = str(host)
		self.port = int(port) #32100
		self.brel_devices = brel_devices
		try:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.s.settimeout(3)
		except socket.error as msg:
			Domoticz.Debug ('Error Code: ' + str(msg))
		return

	def request_device_list(self):
		#Set the whole string
		self.JSON = {}
		self.JSON ['msgType'] = 'GetDeviceList'
		self.JSON ['msgID'] = self.timestamp()
		Domoticz.Debug ('DeviceList Package: ' + str(json.dumps(self.JSON)))

		data = self.send_message()

		if data is not False:
			self.brel_devices['gateway'] = data
			self.brel_devices['devices'] = {}
			try:
				for device in data['data']:
					self.brel_devices['devices'][device['mac']] = {}
					self.brel_devices['devices'][device['mac']]['deviceType'] = device['deviceType']

				return self.brel_devices
			except:
				return False


	def request_device_status(self, Mac=None):
		self.JSON = {}
		self.JSON ['msgType'] = 'ReadDevice'
		self.JSON ['mac'] = Mac
		self.JSON ['deviceType'] = self.brel_devices['devices'][Mac]['deviceType']
		self.JSON ['msgID'] = self.timestamp(Mac)
		Domoticz.Debug ('ReadDevice Package: ' + str(json.dumps(self.JSON)))

		data = self.send_message()

		if data is not False:
			if Mac not in self.brel_devices['devices']:
				self.brel_devices['devices'][Mac] = {}
			self.brel_devices['devices'][Mac] = data

			if 'grp-0' in self.brel_devices['devices']:
				self.brel_devices['devices']['grp-0']['data']['currentPosition'] = data['data']['currentPosition']
				self.brel_devices['devices']['grp-0']['data']['currentAngle'] = data['data']['currentAngle']


			return self.brel_devices
		else:
			return False

	def send_command(self, Mac=None, Commands=None):

		JSON_DATA = {}

		if Commands:
			for com in Commands:
				if com == 'P':
					JSON_DATA ['targetPosition'] = int(Commands['P'])
				if com == 'A':
					JSON_DATA ['targetAngle'] = int(Commands['A'])
		else:
			return False

		self.JSON = {}
		self.JSON ['data'] = JSON_DATA
		self.JSON ['msgType'] = 'WriteDevice'
		self.JSON ['mac'] = Mac
		self.JSON ['deviceType'] = self.brel_devices['devices'][Mac]['deviceType']
		self.JSON ['AccessToken'] = self.brel_devices['AccessToken']
		self.JSON ['msgID'] = self.timestamp(Mac)
		Domoticz.Debug ('WriteDevice Package: ' + str(json.dumps(self.JSON)))

		data = self.send_message()

		if data is not False:
			return data
		else:
			return False

	def send_message(self):
		try:
			self.s.sendto(bytes(json.dumps(self.JSON), encoding='utf8'), (self.host, self.port))
			# self.s.sendto(bytes(json.dumps(MESSAGE)), (self.host, self.port))
			
			# receive data from client (data, addr)
			try:
				reply, addr = self.s.recvfrom(1024)
			except socket.error as msg:
				self.s.close()
				Domoticz.Debug ('Error Code: ' + str(msg))
				Domoticz.Debug ('Is the Device On??')
				return False

			Domoticz.Debug('Server reply: ' + str(reply))

			data = json.loads(reply.decode('utf-8'))
			self.s.close()
			
			return data

		except socket.error as msg:
			self.s.close()
			Domoticz.Debug('Error Code : ' + str(msg[0]) + ' Message ' + str(msg[1]))

		return False

	def timestamp(self, Mac=None):
		msgID = ''
		n = '101'
		if Mac is not None:
			n = re.findall(r'\d+', Mac)[-1]
		msgID = str( n + str(int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000) ))
		return msgID
