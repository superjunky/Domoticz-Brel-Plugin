# A Domoticz plugin for Brel Home Hub

* [Key features](#key-features)
* [Supported Brel devices](#supported-brel-devices)
* [Compatible hardware](#compatible-hardware)
* [Software requirements](#software-requirements)
* [Installation](#installation)
* [Configuration](#configuration)
* [Updating plugin](#updating-plugin)
* [Known issues](#known-issues)
* [Usage](#usage)
  + [Blinds and curtains](#blinds-and-curtains)
  + [Venetian blinds](#venetian-blinds)
* [Bonus: Homebridge](#bonus-homebridge)

## Brel Home Hub
Brel offers some great motors for blinds and screens, for inside and outside use. Now there is a gateway in the form of the Brel Home Hub, which can be controlled from your smartphone. Ofcourse we want Domoticz to be able to communicate with the Home Hub aswel, and now we can!
If you want to know more what the Brel Home Hub is all about, check their website: ([`https://www.brel-motors.nl/brel-app.html`](https://www.brel-motors.nl/brel-app.html)). But for now, let's read ahead and check out this plugin!

## Key features
- Creates devices in Domoticz for every device configured in your Brel Home Hub
- Creates seperate devices for Position and Tilt
- Creates an extra virtual device for controlling áll your devices at once
- Specify default Position and Angle for your devices' Open and Close buttons


## Supported Brel devices
The plugin supports and is able to controll the following devices:
- Bi-Directional devices

The plugin doesn't work with:
- Unknown

## Compatible hardware
Most systems capable of running domoticz and has a version of python3 available should be able to run the plugin.
- Tested on Linux [Synology NAS] only

## Software requirements:
1. Python version 3.5.3 or higher, 3.7.x recommended
2. Domoticz compiled with support for Python-Plugins
3. Upgraded pip
4. You need the pycrypto Python-module

## Installation:
### 1. Clone Brel plugin into domoticz plugins-directory:
```shell
  $ cd domoticz/plugins/
  $ git clone https://github.com/superjunky/Domoticz-Brel-Plugin.git Domoticz-Brel-Plugin
```

### 2. Update pip:
```shell
  $ pip3 install -U pip
```

### 3. Install pycrypto
The plugin uses the pycrypto python module ([`https://pypi.org/project/pycrypto/`](https://pypi.org/project/pycrypto/))

```shell
  $ pip3 install pycrypto
```

#### 3.1 Let Domoticz know about the pycrypto module
Domoticz may not have the path to the pycrypto library in its python environment.
In this case you will observe something starting like that in the log:
* failed to load 'plugin.py', Python Path used was
* Module Import failed, exception: 'ImportError'

To find where pycrypto is installed, in a shell:
```shell
  $ pip3 show pycrypto
```
The Crypto directory should be present in the directory indicated with Location.

When you have it installed, just add a symbolic link to it in Domoticz-Brel-Plugin directory with ```ln -s```.
Example:
```shell
  $ cd ~/domoticz/plugins/Domoticz-Brel-Plugin
  $ ln -s /home/pi/.local/lib/python3.5/site-packages/Crypto Crypto
```

### 4. Restart domoticz and enable Brel Home Hub from the hardware page
Don't forget to enable "Allow new Hardware" in the Domoticz settings page.

## Configuration
- Enter the IP of your Brel Home Hub.
- Enter the KEY of your Brel Home Hub. Get the KEY by quickly tapping 5 times on "Version 1.x.x(x)" in your Brel SmartPhone app. You'll get the 16-byte KEY in a popup, which you can then copy/paste. On Android you'll have to tap next to your profile picture instead of the version-number.
- Don't forget to let Domoticz allow new devices before you activate this plugin!
- Optionally you can specify default positions and/or angle's for your blinds' Open and Close buttons. Similar to a Favorite position. Read on for learning more about this.

#### The "Defaults array" explained
Let's start with an example:
```
  -1:{"o":{"P":15,"A":25},"c":{"P":80,"A":80}}
```
- The first number indicated the Domoticz device ID (idx). You can enter "-1" as a fall-back "default" for ALL devices. Use "0" (zero) for the virtual All-device.
- Next there will be an "o" or a "c", indicating the settings will be for either "open" or "close".
- The open- and close- sets need to have at least one "P" or "A" (or both), to specify the blinds Position and Angle.
- Position values can be 0-100 (%). Angle values can be 0-180 (degrees).
- All values are optional.

In conclusion, a full array could look like this:
```
  -1:{"o":{"P":15,"A":25},"c":{"P":100,"A":90}}, 0:{"o":{"A":25}}, 3:{"c":{"P":80,"A":80}}
```

## Updating plugin
To update the plugin to the newest version, stop domoticz, enter the plugin directory, pull the latest changes from git and restart domoticz:
```shell
  $ cd domoticz/plugins/Domoticz-Brel-Plugin
  $ git pull
```

## Known issues
None so far.

## Usage
Devices have to be added to the gateway as per Brel's instructions, using the official Brel app.

### Blinds and curtains Position
Domoticz sets the position of a blind as a percentage between 0 (fully open) to 100 (fully closed). You need to set the minimum/maximum posistions of the blind before using Domoticz. Please refer to the instructions from Brel on how to set the maximum positions of a blind.

### Venetian blinds Tilt
Besides the position, Domoticz can set the angle of a venetian blind in degrees. An additional device is created, where the name will end with "Tilt". For this device you can set a percentage between 0 and 100, and is converted by the plugin into degrees between 0 and 180. To open your blinds, set the angle to 50% (which translates to 90 degrees).

By default this Tilt-device in Domoticz will send a 90-degrees-command when switched on, and a 0-degrees-command when switched of. Use the slider to choose a custom position.

## Bonus: Homebridge
So, you have Domoticz running at home, AND you have an iPhone? Chances are you have a copy of Homebridge running aswel. Then go ahead:

- Get yourself the MQTTthing-plugin for homebride
- Setup MQTT for Domoticz
- And add the config below to your Homebridge config
- Don't forget to replace `{idx_position}` and `{idx_tilt}` with the idx's of the Domoticz devices...

And there you go, your Brel-blinds can be controlled from within your Apple's Homekit :)

```JSON
{
    "accessory": "mqttthing",
    "type": "windowCovering",
    "name": "{Blinds name}",
    "topics": {
        "getCurrentPosition": {
            "topic": "domoticz/out/mqtt/MQTTthing",
            "apply": "return JSON.parse(message).idx == {idx_position} ? Math.round( 100 - JSON.parse(message).svalue1 ) : undefined"
        },
        "setTargetPosition": {
            "topic": "domoticz/in",
            "apply": "return JSON.stringify({command: 'switchlight', idx: {idx_position}, switchcmd: 'Set Level', level: Math.round( 100 - message ) })"
        },
        "getTargetPosition": {
            "topic": "domoticz/out/mqtt/MQTTthing",
            "apply": "return JSON.parse(message).idx == {idx_position} ? Math.round( 100 - JSON.parse(message).svalue1 ) : undefined"
        },
        "getPositionState": {
            "topic": "domoticz/out/mqtt/MQTTthing",
            "apply": "return JSON.parse(message).idx == {idx_position} || JSON.parse(message).idx == {idx_tilt} ? 'STOPPED' : undefined"
        },
        "setTargetHorizontalTiltAngle": {
            "topic": "domoticz/in",
            "apply": "return JSON.stringify({command: 'switchlight', idx: {idx_tilt}, switchcmd: 'Set Level', level: Math.round( (message + 90) / 1.8) })"
        },
        "getTargetHorizontalTiltAngle": {
            "topic": "domoticz/out/mqtt/MQTTthing",
            "apply": "return JSON.parse(message).idx == {idx_tilt} ? Math.round( (JSON.parse(message).svalue1 * 1.8) - 90 ) : undefined"
        },
        "getCurrentHorizontalTiltAngle": {
            "topic": "domoticz/out/mqtt/MQTTthing",
            "apply": "return JSON.parse(message).idx == {idx_tilt} ? Math.round( (JSON.parse(message).svalue1 * 1.8) - 90 ) : undefined"
        }
    },
    "startPub": [
        {
            "topic": "domoticz/in",
            "message": "{\"command\": \"getdeviceinfo\", \"idx\": {idx_position} }"
        },
        {
            "topic": "domoticz/in",
            "message": "{\"command\": \"getdeviceinfo\", \"idx\": {idx_tilt} }"
        }
    ],
    "manufacturer": "Brel",
    "model": "Venetian Blinds",
    "serialNumber": "Idx {idx_position}"
}
```
