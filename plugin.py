# Brel Home Hub
#
# Author: Superjunky, 2021
#
# INSTALL DEPENDENCY:
# There was some trouble to get Domoticz find the pycrypt module. Here is how I messed around:
# apt-get update
# apt-get install python3-dev
# apt-get install python3-pip
# apt remove python3-crypto
# python3.7 -m pip install pip
# python3.7 -m pip install pycrypt
#
#
"""
<plugin key="Brel-Home-Hub" name="Brel Home Hub" author="Superjunky" version="1.0.0" wikilink="https://github.com/superjunky/Domoticz-Brel-Plugin" externallink="https://www.brel-motors.nl/brel-app.html">
    <description>
        <h2>Brel Home Hub</h2><br/>
        <h3>Features</h3>
        <ul>
	        <li>Creates devices for every device configured in your Brel Home Hub</li>
	        <li>Creates seperate devices for Position and Tilt</li>
	        <li>Creates an extra virtual device for controlling áll your devices at once</li>
	        <li>Specify default Position and Angle for your devices' Open and Close buttons</li>
		</ul>
        <h3>Configuration</h3>
        <ul>
	        <li>Enter the IP of your Brel Home Hub.</li>
	        <li>Enter the KEY of your Brel Home Hub. Get the KEY by quickly tapping 5 times on "Version 1.x.x(x)" in your Brel SmartPhone app. You'll get the 16-byte KEY in a popup, which you can then copy/paste. On Android tap next to the profile picture instead of the version-number.</li>
	        <li>Don't forget to let Domoticz allow new devices before you activate this plugin!</li>
	        <li>Optionally you can specify default positions and/or angle's for your blinds' Open and Close buttons. Similar to a Favorite position. Read on for learning more about this.</li>
		</ul>
        <h3>The "Defaults array" explained</h3>
		Let's start with an example array:<br /><br />
		-1:{"o":{"P":15,"A":25},"c":{"P":80,"A":80}}<br /><br />
		<ul>
			<li>The first number indicated the Domoticz device ID (idx). You can enter "-1" as a fall-back 'default' for ALL devices. Use "0" (zero) for the virtual All-device.</li>
			<li>Next there will be an "o" or a "c", indicating the settings will be for either "open" or "close".</li>
			<li>The open- and close-sets need to have at least one "P" or "A" (or both), to specify the blinds Position and Angle.</li>
			<li>Position values can be 0-100 (%). Angle values can be 0-180 (degrees).</li>
			<li>All values are optional.</li>
		</ul>
		In conclusion, a full array could look like this:<br /><br />
		-1:{"o":{"P":15,"A":25},"c":{"P":100,"A":90}}, 0:{"o":{"A":25}}, 3:{"c":{"P":80,"A":80}}
        <br /><br /><br />
    </description>
	<params>
		<param field="Address" label="Remote address" width="300px" required="true" default="127.0.0.1"/>
		<param field="Mode1" label="Key" width="300px" required="true" default=""/>
		<param field="Mode2" label="Defaults" width="500px" default=""/>
		<param field="Mode6" label="Debug" width="75">
			<options>
				<option label="True" value="Debug"/>
				<option label="False" value="Normal"  default="true" />
			</options>
		</param>
	</params>
</plugin>
"""
import threading
import Domoticz
from brel import brel
from Crypto.Cipher import AES
import binascii
import datetime

class BasePlugin:
	u_port = 32100 # unicast
	m_port = 32101 # multicast
	enabled = False

	BrelConn = None

	brel_devices = {}
	DeviceIDdict = {}

	overrideGrpCommands = 0

	lastPollTime = None
	pollInterval = None

	hasTimedOut = False
	commandQueue = []

	def __init__(self):
		return

	def GenerateAccessToken(self):

		try:
			if 'token' in self.brel_devices['gateway']:
				key = Parameters['Mode1']
				token = self.brel_devices['gateway']['token']
				cipher = AES.new(key, AES.MODE_ECB)
				AccessToken = binascii.hexlify(cipher.encrypt(token)).decode('utf-8')
				self.brel_devices['AccessToken'] = AccessToken.upper()

			return self.brel_devices['AccessToken']

		except:
			return Error

	def indexRegisteredDevices(self):

		if len(Devices) > 0:
			# Some devices are already defined

			try:
				for aUnit in Devices:
					dev_id = Devices[aUnit].DeviceID.split("-")

					if len(dev_id) > 1 and dev_id[0] == "grp":
						self.updateDevice(aUnit, override_level=None, Report=True)
					else:
						self.updateDevice(aUnit)

				return [dev.DeviceID for key, dev in Devices.items()]

			except (HandshakeError, ReadTimeoutError, WriteTimeoutError):
				self.hasTimedOut = True
				return
			else:
				self.hasTimedOut = False
		else:
			deviceID = [-1]
			return deviceID

	def updateDevice(self, Unit, override_level=None, Report=None):

		deviceUpdated = False

		try:
			devID = str(Devices[Unit].DeviceID).split(":")[0]
			if devID in self.brel_devices['devices']:
				if Report is None:
					brel_api = brel(Parameters['Address'], self.u_port, self.brel_devices)
					self.brel_devices = brel_api.request_device_status(devID)

				brel_device = {}
				brel_device = self.brel_devices['devices'][devID]
			else:
				return
		except TypeError:
			self.hasTimedOut = True
			return

		if Devices[Unit].Type == 244:

			# Switches
			if Devices[Unit].SwitchType == 0:
				# On/off - device
				if (Devices[Unit].nValue != brel_device.State) or (
					Devices[Unit].sValue != str(brel_device.Level)
				):
					Devices[Unit].Update(
						nValue=brel_device.State,
						sValue=str(brel_device.Level),
					)

			elif Devices[Unit].SwitchType == 13 or Devices[Unit].SwitchType == 7:
				# Blinds 0=Open 1=Dicht 2=%
				if Devices[Unit].DeviceID[-2:] == ':P':
					position = brel_device['data']['currentPosition']
					if Devices[Unit].sValue != str(position):

						if int(position) < 1:
							nValue = 0
						elif int(position) > 99:
							nValue = 1
						else:
							nValue = 2

						Devices[Unit].Update(
							nValue=nValue,
							sValue=str(position),
							SignalLevel=RSSItoLevel(brel_device['data']['RSSI'])
						)
						deviceUpdated = True

				# Dimmer 0=Off 1=On 2=%
				if Devices[Unit].DeviceID[-2:] == ':A':
					angle = (100/180) * int(brel_device['data']['currentAngle'])
					if Devices[Unit].sValue != str(angle):
						if int(angle) < 1:
							nValue = 0
						elif int(angle) > 99:
							nValue = 1
						else:
							nValue = 2

						Devices[Unit].Update(
							nValue=nValue,
							sValue=str(angle),
							SignalLevel=RSSItoLevel(brel_device['data']['RSSI'])
						)
						deviceUpdated = True

		self.hasTimedOut = False

		return deviceUpdated

	def registerDevices(self):

		self.brel_devices = {}

		try:
			# Get the token and device list
			brel_api = brel(Parameters['Address'], self.u_port, self.brel_devices)
			self.brel_devices = brel_api.request_device_list()

			if 'grp-0' not in self.brel_devices['devices']:
				# Add group-devices to self.brel_devices
				self.brel_devices['devices']['grp-0'] = { 'mac': 'grp-0', 'deviceType': 'group', 'data': { 'currentPosition': 0, 'currentAngle': 0, 'RSSI': 12 } }
		except:
			Domoticz.Debug('Connection to gateway timed out')
			self.hasTimedOut = True
			return

		if self.hasTimedOut:
			return

		# Generate the AccessToken
		try:
			AccessToken = self.GenerateAccessToken()
			Domoticz.Status('AccessToken {} generated.'.format(AccessToken))
		except:
			Domoticz.Error('AccessToken could not be generated.')
			self.hasTimedOut = True
			return

		if self.hasTimedOut:
			return

		unitIds = self.indexRegisteredDevices()
		name_number = 0

		# Add unregistred brel_devices
		for brel_device in self.brel_devices['devices']:

			devID = str(brel_device)
			devType = str(self.brel_devices['devices'][brel_device]['deviceType'])

			if devType != '02000001': # Gateway

				if devType == 'group':
					name = 'Group All'
					report = True
				else:
					name = 'Blinds {}'
					report = None

					if devID + ":P" not in unitIds or devID + ":A" not in unitIds:
						if len(Devices) > 0:
							name_number = int(len(Devices) / 2)
						name_number = name_number + 1
						name = name.format(name_number)

				if devID + ":P" not in unitIds:
					new_unit_id = firstFree()
					Domoticz.Device(
						Name=name,
						Unit=new_unit_id,
						Type=244,
						Subtype=73,
						Switchtype=13,
						DeviceID=devID + ":P",
						Used=1,
					).Create()
					self.updateDevice(new_unit_id, None, Report=report)

				if devID + ":A" not in unitIds:
					new_unit_id = firstFree()
					Domoticz.Device(
						Name=name + " Tilt",
						Unit=new_unit_id,
						Type=244,
						Subtype=73,
						Switchtype=7,
						DeviceID=devID + ":A",
						Used=1,
					).Create()
					self.updateDevice(new_unit_id, None, Report=report)

		self.hasTimedOut = False

	def onStart(self):

		try:
			if Parameters["Mode6"] == "Debug":
				Domoticz.Debugging(1)
				DumpConfigToLog()
				logFile = open(Parameters["HomeFolder"]+Parameters["Key"]+".log",'w')
		except ValueError:
			Domoticz.Debugging(0)

		self.lastPollTime = datetime.datetime.now()
		self.pollInterval = 3600

		# Create some devices if needed
		try:
			self.registerDevices()
			Domoticz.Status('Brel module successfully initialized!')
		except:
			Domoticz.Error('Failed to initialize Brel module.')

		Domoticz.Debug('If you like to debug, check the brel_devices: {}'.format(self.brel_devices))

		# A reverse Device ID to Unit list
		for x in Devices:
			self.DeviceIDdict[Devices[x].DeviceID] = x

		# Go ahead and UDP' the hell out of it
		self.BrelConn = Domoticz.Connection(Name="Brel", Transport="UDP/IP", Protocol="JSON", Address="238.0.0.18", Port=str(self.m_port))
		self.BrelConn.Listen()

	def onStop(self):
		Domoticz.Debug("Stopping BREL plugin")

		if Parameters["Mode6"] == "Debug":
			pass
			# Domoticz.Debug("Stopping observe")
			# observe_stop()

		Domoticz.Debug("Threads still active: " + str(threading.active_count()) + ", should be 1.")
		while threading.active_count() > 1:
			for thread in threading.enumerate():
				if thread.name != threading.current_thread().name:
					Domoticz.Debug("'" + thread.name + "' is still running, waiting otherwise Domoticz will crash on plugin exit.")
			time.sleep(1.0)

		Domoticz.Debugging(0)

	def onConnect(self, Connection, Status, Description):
		Domoticz.Debug("onConnect called")

	def onMessage(self, Connection, Data):
		Domoticz.Debug("onMessage called")

		try:

			if Data['msgType'] == 'Report':
				Mac = Data['mac']

				if Data['deviceType'] != 'group' and Data['deviceType'] != '02000001':
					if Mac not in self.brel_devices['devices']:
						self.brel_devices['devices'][Mac] = {}

					self.brel_devices['devices'][Mac]['data'] = Data['data']

					# And also update the "All" devices to reflect the positions of last updated device
					self.brel_devices['devices']['grp-0']['data']['currentPosition'] = Data['data']['currentPosition']
					self.brel_devices['devices']['grp-0']['data']['currentAngle'] = Data['data']['currentAngle']

					Unit = int(self.DeviceIDdict[str(Mac)+':P'])
					self.updateDevice(Unit, None, True)
					Unit = int(self.DeviceIDdict[str(Mac)+':A'])
					self.updateDevice(Unit, None, True)

					if self.overrideGrpCommands > 0:
						self.overrideGrpCommands = self.overrideGrpCommands - 1
					else:
						Unit = int(self.DeviceIDdict['grp-0'+':P'])
						self.updateDevice(Unit, None, True)
						Unit = int(self.DeviceIDdict['grp-0'+':A'])
						self.updateDevice(Unit, None, True)

			Domoticz.Debug(Connection.Name + ": " + str(Data))

		except Exception as inst:
			# Domoticz.Error("Exception in onMessage, called with Data: '"+str(strData)+"'")
			Domoticz.Error("Exception detail: '"+str(inst)+"'")
			raise

	def onCommand(self, Unit, Command, Level, Hue):
		Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

		devID = str(Devices[Unit].DeviceID).split(":")[0]
		devType = str(self.brel_devices['devices'][devID]['deviceType'])
		devCommands = {}

		if Command == "On" or Command == "Off":
			if Parameters['Mode2']:
				try:
					defaults = eval('{'+str(Parameters['Mode2'])+'}')
				except:
					defaults = {}

			if devID == 'grp-0':
				idx = 0
			else:
				idx = Devices[Unit].ID

			if idx not in defaults:
				if -1 in defaults:
					idx = -1

		# if len(defaults) < 1:
		# 	defaults = eval("{0:{1:{'P':15,'A':25},0:{'P':80,'A':80}},1:{1:{'P':15,'A':25},0:{'P':80,'A':80}},3:{1:{'P':15,'A':25},0:{'P':80,'A':80}}}")

		try:
			if Command == "On": # closed
				if Devices[Unit].DeviceID[-2:] == ':P':
					try:
						if idx in defaults:
							for com in defaults[idx]['c']:
								devCommands[com] = defaults[idx]['c'][com]
						else:
							Error
					except:
						devCommands['P'] = 100

				if Devices[Unit].DeviceID[-2:] == ':A':
					devCommands['A'] = 80 # 90 degrees = open

			elif Command == "Off": # open
				if Devices[Unit].DeviceID[-2:] == ':P':
					try:
						if idx in defaults:
							for com in defaults[idx]['o']:
								devCommands[com] = defaults[idx]['o'][com]
						else:
							Error
					except:
						devCommands['P'] = 0

				if Devices[Unit].DeviceID[-2:] == ':A':
					devCommands['A'] = 0

			elif Command == "Set Level":
				Domoticz.Debug("Command Level: {}".format(Level))
				newLevel = int(Level)

				if newLevel not in range(0, 101):
					newLevel = 100 if newLevel > 100 else 0

				if Devices[Unit].DeviceID[-2:] == ':P':
					devCommands['P'] = str(newLevel)

				if Devices[Unit].DeviceID[-2:] == ':A':
					newLevel = round((180 / 100) * newLevel)
					devCommands['A'] = str(newLevel)

			if devCommands:
				if 'P' in devCommands:
					self.brel_devices['devices'][devID]['data']['currentPosition'] = devCommands['P']
				if 'A' in devCommands:
					self.brel_devices['devices'][devID]['data']['currentAngle'] = devCommands['A']

				if devID == 'grp-0':
					for brel_device in self.brel_devices['devices']:
						if self.brel_devices['devices'][brel_device]['deviceType'] != 'group' and self.brel_devices['devices'][brel_device]['deviceType'] != '02000001': # Gateway::

							if 'P' in devCommands:
								self.brel_devices['devices'][brel_device]['data']['currentPosition'] = devCommands['P']
							if 'A' in devCommands:
								self.brel_devices['devices'][brel_device]['data']['currentAngle'] = devCommands['A']

							brel_api = brel(Parameters['Address'], self.u_port, self.brel_devices)
							brel_command_ack = brel_api.send_command(brel_device, devCommands)

							self.overrideGrpCommands = self.overrideGrpCommands + 1

							for com in devCommands:
								self.updateDevice(int(self.DeviceIDdict[brel_device+':'+com]), None, Report=True)

				else:
					brel_api = brel(Parameters['Address'], self.u_port, self.brel_devices)
					brel_command_ack = brel_api.send_command(devID, devCommands)

				for com in devCommands:
					self.updateDevice(int(self.DeviceIDdict[devID+':'+com]), None, Report=True)

			Domoticz.Debug("Finnished command")

		except KeyError:
			Domoticz.Error(
				"OnCommand failed for device: {} with command: {} and level: {}".format(
					devID, Command, Level
				)
			)

		except:
			comObj = {"Unit": Unit, "Command": Command, "Level": Level}
			Domoticz.Debug(
				"Command timed out. Pushing {} onto commandQueue".format(comObj)
			)
			self.commandQueue.append(comObj)

	def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
		Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

		devID = int(str(Devices[Unit].DeviceID).split(":")[0])

	def onDisconnect(self, Connection):
		Domoticz.Log("onDisconnect called")
		self.isConnected = False 

	def onHeartbeat(self):
		Domoticz.Debug("onHeartBeat called")

		for aCommand in self.commandQueue:
			Domoticz.Log("Command in queue")
			Domoticz.Debug("Trying to execute {} from commandQueue".format(aCommand))
			self.commandQueue.remove(aCommand)
			self.onCommand(
				aCommand["Unit"], aCommand["Command"], aCommand["Level"], None
			)

		if self.hasTimedOut:
			Domoticz.Error("Timeout flag set, retrying...")
			self.hasTimedOut = False
			self.registerDevices()
		else:
			if self.lastPollTime is None:
				self.lastPollTime = datetime.datetime.now()
			else:
				interval = (datetime.datetime.now() - self.lastPollTime).seconds
				if interval + 1 > self.pollInterval:
					self.lastPollTime = datetime.datetime.now()
					self.indexRegisteredDevices()


global _plugin
_plugin = BasePlugin()

def onStart():
	global _plugin
	_plugin.onStart()

def onStop():
	global _plugin
	_plugin.onStop()

def onConnect(Connection, Status, Description):
	global _plugin
	_plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
	global _plugin
	_plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
	global _plugin
	_plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
	global _plugin
	_plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
	global _plugin
	_plugin.onDisconnect(Connection)

def onHeartbeat():
	global _plugin
	_plugin.onHeartbeat()

# Configuration Helpers
def getConfigItem(Key=None, Default={}):
    Value = Default
    try:
        Config = Domoticz.Configuration()
        if (Key != None):
            Value = Config[Key] # only return requested key if there was one
        else:
            Value = Config      # return the whole configuration if no key
    except KeyError:
        Value = Default
    except Exception as inst:
        Domoticz.Error("Domoticz.Configuration read failed: '"+str(inst)+"'")
    return Value
    
def setConfigItem(Key=None, Value=None):
    Config = {}
    try:
        Config = Domoticz.Configuration()
        if (Key != None):
            Config[Key] = Value
        else:
            Config = Value  # set whole configuration if no key specified
        Domoticz.Configuration(Config)
    except Exception as inst:
        Domoticz.Error("Domoticz.Configuration operation failed: '"+str(inst)+"'")
    return Config

# Generic helper functions
def DumpConfigToLog():
	for x in Parameters:
		if Parameters[x] != "":
			Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
	Domoticz.Debug("Device count: " + str(len(Devices)))
	for x in Devices:
		Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
		Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
		Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
		Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
		Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
		Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
	return

def firstFree():
	for num in range(1, 250):
		if num not in Devices:
			return num
	return

def RSSItoLevel(RSSI):
	if RSSI == 12:
		level = 12
	elif RSSI > -50:
		level = 10
	elif RSSI < -98:
		level = 0
	else:
		level = ((RSSI + 97) /5 ) +1
	return int(level)
