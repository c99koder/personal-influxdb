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

import requests, requests_cache, sys, math
from datetime import datetime, date, timedelta
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

EDSM_API_KEY = ''
EDSM_COMMANDER_NAME = ''
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'edsm'
points = []
last = None

def add_rank(data, activity):
    global points
    points.append({
        "measurement": "rank",
        "time": date.today().isoformat() + "T00:00:00",
        "tags": {
            "commander": EDSM_COMMANDER_NAME,
            "activity": activity
        },
        "fields": {
            "value": data['ranks'][activity],
            "progress": data['progress'][activity],
            "name": data['ranksVerbose'][activity]
        }
    })

def fetch_system(name):
    try:
        response = requests.get('https://www.edsm.net/api-v1/system',
            params={'systemName':name, 'showCoordinates':1, 'showPrimaryStar':1, 'apiKey':EDSM_API_KEY})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("HTTP request failed: %s" % (err))
        sys.exit()

    return response.json()

def distance(system1, system2):
    s1 = fetch_system(system1)
    s2 = fetch_system(system2)

    dx = float(s1['coords']['x']) - float(s2['coords']['x'])
    dy = float(s1['coords']['y']) - float(s2['coords']['y'])
    dz = float(s1['coords']['z']) - float(s2['coords']['z'])

    return math.sqrt(dx*dx + dy*dy + dz*dz)

def add_jump(src, dst):
    global points
    system = fetch_system(dst['system'])
    if 'type' in system['primaryStar']:
        points.append({
            "measurement": "jump",
            "time": datetime.fromisoformat(dst['date']).isoformat(),
            "tags": {
                "commander": EDSM_COMMANDER_NAME,
                "system": dst['system'],
                "firstDiscover": dst['firstDiscover'],
                "primaryStarType": system['primaryStar']['type']
            },
            "fields": {
                "distance": distance(src['system'], dst['system']),
                "x": float(system['coords']['x']),
                "y": float(system['coords']['y']),
                "z": float(system['coords']['z'])
            }
        })
    else:
        points.append({
            "measurement": "jump",
            "time": datetime.fromisoformat(dst['date']).isoformat(),
            "tags": {
                "commander": EDSM_COMMANDER_NAME,
                "system": dst['system'],
                "firstDiscover": dst['firstDiscover']
            },
            "fields": {
                "distance": distance(src['system'], dst['system']),
                "x": float(system['coords']['x']),
                "y": float(system['coords']['y']),
                "z": float(system['coords']['z'])
            }
        })

def fetch_jumps(time):
    global last
    try:
        response = requests.get('https://www.edsm.net/api-logs-v1/get-logs',
            params={'commanderName':EDSM_COMMANDER_NAME, 'apiKey':EDSM_API_KEY, 'endDateTime':time})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("HTTP request failed: %s" % (err))
        sys.exit()

    data = response.json()
    print("Got %s jumps from EDSM" % (len(data['logs'])))

    for jump in data['logs']:
        if last != None:
            add_jump(jump, last)
        last = jump

    return data

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(INFLUXDB_DATABASE)
    client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

try:
    response = requests.get('https://www.edsm.net/api-commander-v1/get-credits',
        params={'commanderName':EDSM_COMMANDER_NAME, 'apiKey':EDSM_API_KEY})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print("HTTP request failed: %s" % (err))
    sys.exit()

data = response.json()
print("Got credits from EDSM")

for credits in data['credits']:
    points.append({
        "measurement": "credits",
        "time": datetime.fromisoformat(credits['date']).isoformat(),
        "tags": {
            "commander": EDSM_COMMANDER_NAME
        },
        "fields": {
            "value": credits['balance']
        }
    })

try:
    response = requests.get('https://www.edsm.net/api-commander-v1/get-ranks',
        params={'commanderName':EDSM_COMMANDER_NAME, 'apiKey':EDSM_API_KEY})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print("HTTP request failed: %s" % (err))
    sys.exit()

data = response.json()
print("Got ranks from EDSM")
add_rank(data, "Combat")
add_rank(data, "Trade")
add_rank(data, "Explore")
add_rank(data, "CQC")
add_rank(data, "Federation")
add_rank(data, "Empire")

requests_cache.install_cache('edsm')
data = fetch_jumps(date.today().isoformat() + " 00:00:00")
if len(data['logs']) > 0:
    data = fetch_jumps(data['startDateTime'])
    while len(data['logs']) == 0:
        data = fetch_jumps(data['startDateTime'])

try:
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))
