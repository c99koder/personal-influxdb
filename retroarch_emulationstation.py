#!/usr/bin/python3

#  Copyright (C) 2021 Sam Steele
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os, ntpath, json, pytz, urllib
import xml.etree.ElementTree as ET
from datetime import datetime
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

LOCAL_TIMEZONE = pytz.timezone('America/New_York')
RETROARCH_LOGS = '/home/ark/.config/retroarch/playlists/logs/'
EMULATIONSTATION_ROMS = '/roms'
IMAGE_WEB_PREFIX = 'https://example.net/retroarch_images/'
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'gaming'
points = []

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(INFLUXDB_DATABASE)
    client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

roms = {}
for platform in os.listdir(EMULATIONSTATION_ROMS):
	if os.path.exists(EMULATIONSTATION_ROMS + '/' + platform + '/gamelist.xml'):
		gamelist = ET.parse(EMULATIONSTATION_ROMS + '/' + platform + '/gamelist.xml').getroot()
		for game in gamelist.findall('game'):
			if gamelist.find('provider/System') != None:
				rom = {}
				rom['name'] = game.find('name').text
				rom['filename'] = ntpath.basename(game.find('path').text)
				rom['key'] = os.path.splitext(rom['filename'])[0]
				rom['path'] = platform
				rom['platform'] = gamelist.find('provider/System').text
				if(rom['platform'] == 'Mame'):
					rom['platform'] = 'Arcade'

				roms[rom['key']] = rom

for core in os.listdir(RETROARCH_LOGS):
	totals = client.query('SELECT last("total") AS "total" FROM "time" WHERE "total" > 0 AND "player_id" = \'' + core + '\' GROUP BY "application_id" ORDER BY "time" DESC')

	for log in os.listdir(RETROARCH_LOGS + '/' + core):
		key = os.path.splitext(log)[0]
		if key in roms:
			with open(RETROARCH_LOGS + '/' + core + '/' + log, 'r') as f:
				playtime = json.load(f)

			rom = roms[key]
			h, m, s = playtime['runtime'].split(':')
			runtime = value = int(h) * 3600 + int(m) * 60 + int(s)
			total = list(totals.get_points(tags={'application_id': rom['key']}))
			if len(total) == 1 and total[0]['total'] > 0:
				value -= total[0]['total']
			if value > 1:
				time = datetime.fromisoformat(playtime['last_played'])
				utc_time = LOCAL_TIMEZONE.localize(time).astimezone(pytz.utc).isoformat()
				points.append({
					"measurement": "time",
					"time": utc_time,
					"tags": {
						"player_id": core,
						"application_id": rom['key'],
						"platform": rom['platform'],
						"player_name": core,
						"title": rom['name'],
					},
					"fields": {
						"value": int(value),
						"total": runtime,
						"image": IMAGE_WEB_PREFIX + urllib.parse.quote_plus(rom['path']) + '/' + urllib.parse.quote_plus(rom['key']) + '.png',
						"url": 'https://thegamesdb.net/search.php?name=' + urllib.parse.quote_plus(rom['name'])
					}
			    })

try:
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print(points)
print("Successfully wrote %s data points to InfluxDB" % (len(points)))
