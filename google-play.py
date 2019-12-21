#!/usr/bin/python3

#  Copyright (C) 2019 Sam Steele
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

import requests, sys, os, re
from datetime import datetime, date, timedelta
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from bs4 import BeautifulSoup

INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'gaming'
points = []

def parse_activity(game):
    file = open('Takeout/Google Play Games Services/Games/' + game + '/Activity.html')
    html = BeautifulSoup(file, 'html.parser')
    file.close()

    for row in html.find_all('tr'):
        if row.contents[0].name == 'td' and row.contents[0].string == 'Time Last Played':
            points.append({
                    "measurement": "time",
                    "time": row.contents[1].string,
                    "tags": {
                        "platform": "Google Play",
                        "title": game,
                    },
                    "fields": {
                        "value": 0
                    }
                })

def parse_achievements(game):
    file = open('Takeout/Google Play Games Services/Games/' + game + '/Experience.html')
    html = BeautifulSoup(file, 'html.parser')
    file.close()

    for row in html.find_all('tr'):
        if row.contents[0].name == 'td' and row.contents[0].string == 'Achievement unlocked':
            date = row.contents[2].string
            game = row.contents[6].string
            achievement = row.contents[1].string.title()
            apiname = row.contents[1].string

            points.append({
                    "measurement": "achievement",
                    "time": date,
                    "tags": {
                        "platform": "Google Play",
                        "title": game,
                        "apiname": apiname
                    },
                    "fields": {
                        "name": achievement
                    }
                })

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(INFLUXDB_DATABASE)
    client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

for game in os.listdir('Takeout/Google Play Games Services/Games/'):
    if os.path.isfile('Takeout/Google Play Games Services/Games/' + game + '/Activity.html'):
        parse_activity(game)
    if os.path.isfile('Takeout/Google Play Games Services/Games/' + game + '/Experience.html'):
        parse_achievements(game)

try:
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))
