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

RA_API_KEY = ''
RA_USERNAME = ''
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

end = datetime.utcnow().timestamp()
start = end - 604800

try:
    response = requests.get('https://retroachievements.org/API/API_GetAchievementsEarnedBetween.php?z=' + RA_USERNAME + '&y=' + RA_API_KEY + '&u=' + RA_USERNAME +'&f=' + str(start) + '&t=' + str(end))
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print("HTTP request failed: %s" % (err))
    sys.exit()

data = response.json()
print("Got %s achievements from RetroAchievements" % len(data))

for achievement in data:
    date = datetime.strptime(achievement['Date'], "%Y-%m-%d %H:%M:%S")

    points.append({
            "measurement": "achievement",
            "time": date.isoformat(),
            "tags": {
                "player_id": RA_USERNAME,
                "platform": achievement['ConsoleName'],
                "player_name": RA_USERNAME,
                "title": achievement['GameTitle'],
                "application_id": str(achievement['GameID']),
                "apiname": str(achievement['AchievementID']),
            },
            "fields": {
                "name": achievement['Title'],
                "description": achievement['Description'],
                "icon": 'https://retroachievements.org' + achievement['BadgeURL']
            }
    })

try:
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))
