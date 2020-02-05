#!/usr/bin/python3

#  Copyright (C) 2020 Sam Steele
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

import requests, pytz, sys
from datetime import datetime, date, timedelta, time
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

LOCAL_TIMEZONE = pytz.timezone('America/New_York')
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
GAMING_DATABASE = 'gaming'
RESCUETIME_DATABASE = 'rescuetime'

games = {
  "angry-birds-vr-isle-of-pigs": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/1001140/header.jpg',
    "title": "Angry Birds VR: Isle of Pigs",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/1001140/'
  },
  "arcade": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/435490/header.jpg',
    "title": "Pierhead Arcade",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/435490/'
  },
  "cloudlands": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/425720/header.jpg',
    "title": "Cloudlands: VR Minigolf",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/425720/'
  },
  "fuji": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/589040/header.jpg',
    "title": "Fuji",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/589040/'
  },
  "half + half": {
    "image": 'https://halfandhalf.fun/assets/images/logo.png',
    "title": "Half + Half",
    "platform": "Oculus",
    "url": 'https://www.oculus.com/experiences/quest/2035353573194060/'
  },
  "openttd": {
    "image": 'https://www.openttd.org/static/img/layout/openttd-128.gif',
    "title": "OpenTTD",
    "platform": "Mac",
    "url": 'https://www.openttd.org'
  },
  "pixelripped1989": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/577530/header.jpg',
    "title": "Pixel Ripped 1989",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/577530/'
  },
  "proze-win64-shipping": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/924250/header.jpg',
    "title": "Proze: Enlightenment",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/924250/'
  },
  "shenmue3-win64-shipping": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/878670/header.jpg',
    "title": "Shenmue III",
    "platform": "Epic Games Store",
    "url": 'https://store.steampowered.com/app/878670/'
  },
  "starcitizen": {
    "image": 'https://robertsspaceindustries.com/rsi/static/wsc/images/Logo-SC@2x.png',
    "title": "Star Citizen",
    "platform": "Windows",
    "url": 'https://robertsspaceindustries.com/star-citizen'
  },
  "synthriders": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/885000/header.jpg',
    "title": "Synth Riders",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/885000/'
  },
  "the sims 4": {
    "image": 'https://media.contentapi.ea.com/content/dam/eacom/SIMS/brand-refresh-assets/images/2019/06/ts4-adaptive-logo-primary-white-7x2-xl-5x2-lg-2x1-md-16x9-sm-xs.png',
    "title": "The Sims 4",
    "platform": "Origin",
    "url": 'https://www.ea.com/games/the-sims/the-sims-4'
  },
  "transpose": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/835950/header.jpg',
    "title": "Transpose",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/835950/'
  },
  "twilightpath_Viveport": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/770110/header.jpg',
    "title": "Twilight Path",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/770110/'
  },
}
points = []
start_time = str(int(LOCAL_TIMEZONE.localize(datetime.combine(date.today(), time(0,0)) - timedelta(days=7)).astimezone(pytz.utc).timestamp()) * 1000) + 'ms'

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(GAMING_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

client.switch_database(RESCUETIME_DATABASE)
durations = client.query('SELECT "duration","activity" FROM "activity" WHERE time >= ' + start_time)
for duration in list(durations.get_points()):
    if duration['activity'] in games:
        points.append({
            "measurement": "time",
            "time": duration['time'],
            "tags": {
                "application_id": duration['activity'],
                "platform": games[duration['activity']]['platform'],
                "title": games[duration['activity']]['title'],
            },
            "fields": {
                "value": duration['duration'],
                "image": games[duration['activity']]['image'],
                "url": games[duration['activity']]['url']
            }
        })

try:
    client.switch_database(GAMING_DATABASE)
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))
