#!/usr/bin/python3
# Copyright 2022 Sam Steele
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, sys
import xml.etree.ElementTree as ET
from datetime import datetime
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
GAMING_DATABASE = 'gaming'

f = open('/run/shm/influx-retropie', 'r')
start = datetime.utcfromtimestamp(int(f.readline().strip()))
platform = f.readline().strip()
emulator = f.readline().strip()
rom = name = os.path.basename(f.readline().strip())
end = datetime.utcfromtimestamp(int(f.readline().strip()))
duration = (end - start).seconds
f.close()

if not rom:
	rom = name = emulator
	platform = "Linux"

#Ignore games played less than 60 seconds
if duration < 60:
	print("Ignoring '" + emulator + ": " + name +"' played less than 60 seconds")
	sys.exit()

#Ignore non-games and Macintosh platform which doesn't provide game names
if platform == "macintosh" or rom.startswith("+") or rom == "Desktop.sh" or rom == "Kodi.sh" or rom == "Steam Link.sh":
	print("Ignoring non-game: '" + emulator + ": " + name +"'")
	sys.exit()

gamelist = os.path.expanduser('~/.emulationstation/gamelists/' + platform + '/gamelist.xml')

if os.path.exists(gamelist):
	root = ET.parse(gamelist).getroot()
	for game in root.findall('game'):
		path = os.path.basename(game.find('path').text)
		if path == name:
			name = game.find('name').text
			break

if platform == "nes":
	platform = "NES"
elif platform == "snes":
	platform = "SNES"
elif platform == "gba":
	platform = "Game Boy Advance"
elif platform == "gbc":
	platform = "Game Boy Color"
elif platform == "megadrive" or platform == "genesis":
	platform = "Sega Genesis"
elif platform == "sega32x":
	platform = "Sega 32X"
elif platform == "segacd":
	platform = "Sega CD"
elif platform == "pc":
	platform = "MS-DOS"
elif platform == "scummvm":
	platform = "ScummVM"
elif platform == "mame-libretro":
	platform = "Arcade"
elif platform == "mastersystem":
	platform = "Sega MasterSystem"
else:
	platform = platform.capitalize()

url = ""
image = ""

if name == "openttd":
	name = "OpenTTD"
	url = "https://www.openttd.org"
	image = "https://www.openttd.org/static/img/layout/openttd-128.gif"

if url and image:
	points = [{
		"measurement": "time",
		"time": start,
		"tags": {
			"application_id": rom,
			"platform": platform,
			"title": name,
		},
		"fields": {
			"value": duration,
			"image": image,
			"url": url
		}
	}]
else:
	points = [{
		"measurement": "time",
		"time": start,
		"tags": {
			"application_id": rom,
			"platform": platform,
			"title": name,
		},
		"fields": {
			"value": duration
		}
	}]

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(GAMING_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

try:
    client.switch_database(GAMING_DATABASE)
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))
