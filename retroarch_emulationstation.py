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

import os, ntpath, json, pytz, urllib
import xml.etree.ElementTree as ET
from datetime import datetime
from config import *

if not os.path.isdir(EMULATIONSTATION_ROMS):
	logging.error("Unable to find path: %s", EMULATIONSTATION_ROMS)
	sys.exit(1)

points = []
client = connect(GAMING_DATABASE)

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
	totals = client.query(f'SELECT last("total") AS "total" FROM "time" WHERE "total" > 0 AND "player_id" = \'{core}\' GROUP BY "application_id" ORDER BY "time" DESC')

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
						"image": f"{RETROARCH_IMAGE_WEB_PREFIX}{urllib.parse.quote(rom['path'])}/{urllib.parse.quote(rom['key'])}.png",
						"url": f"https://thegamesdb.net/search.php?name={urllib.parse.quote_plus(rom['name'])}"
					}
			    })

write_points(points)
