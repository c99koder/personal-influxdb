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

import requests, sys
from datetime import datetime, date, timedelta
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

DEVICE_ID = ''
SMART_DEVICE_ID = ''
SESSION_TOKEN = ''
CLIENT_ID = ''
GRANT_TYPE = 'urn:ietf:params:oauth:grant-type:jwt-bearer-session-token'
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'gaming'
points = []

# These occasionally need to be updated when Nintendo changes the minimum allowed version
INTERNAL_VERSION = '303'
DISPLAY_VERSION = '1.15.0'
OS_VERSION = '14.2'

def get_access_token():
    response = requests.post('https://accounts.nintendo.com/connect/1.0.0/api/token', data={
        'session_token': SESSION_TOKEN,
        'client_id': CLIENT_ID,
        'grant_type': GRANT_TYPE
    })
    return response.json()


def get_daily_summary(access):
    response = requests.get('https://api-lp1.pctl.srv.nintendo.net/moon/v1/devices/' + DEVICE_ID + '/daily_summaries', headers={
        'x-moon-os-language': 'en-US',
        'x-moon-app-language': 'en-US',
        'authorization': access['token_type'] + ' ' + access['access_token'],
        'x-moon-app-internal-version': INTERNAL_VERSION,
        'x-moon-app-display-version': DISPLAY_VERSION,
        'x-moon-app-id': 'com.nintendo.znma',
        'x-moon-os': 'IOS',
        'x-moon-os-version': OS_VERSION,
        'x-moon-model': 'iPhone11,8',
        'accept-encoding': 'gzip;q=1.0, compress;q=0.5',
        'accept-language': 'en-US;q=1.0',
        'user-agent': 'moon_ios/' + DISPLAY_VERSION + ' (com.nintendo.znma; build:' + INTERNAL_VERSION + '; iOS ' + OS_VERSION + ') Alamofire/4.8.2',
        'x-moon-timezone': 'America/Los_Angeles',
        'x-moon-smart-device-id': SMART_DEVICE_ID
    })
    return response.json()

def get_monthly_summary(month, access):
    response = requests.get('https://api-lp1.pctl.srv.nintendo.net/moon/v1/devices/' + DEVICE_ID + '/monthly_summaries/' + month, headers={
        'x-moon-os-language': 'en-US',
        'x-moon-app-language': 'en-US',
        'authorization': access['token_type'] + ' ' + access['access_token'],
        'x-moon-app-internal-version': INTERNAL_VERSION,
        'x-moon-app-display-version': DISPLAY_VERSION,
        'x-moon-app-id': 'com.nintendo.znma',
        'x-moon-os': 'IOS',
        'x-moon-os-version': OS_VERSION,
        'x-moon-model': 'iPhone11,8',
        'accept-encoding': 'gzip;q=1.0, compress;q=0.5',
        'accept-language': 'en-US;q=1.0',
        'user-agent': 'moon_ios/' + DISPLAY_VERSION + ' (com.nintendo.znma; build:' + INTERNAL_VERSION + '; iOS ' + OS_VERSION + ') Alamofire/4.8.2',
        'x-moon-timezone': 'America/Los_Angeles',
        'x-moon-smart-device-id': SMART_DEVICE_ID
    })
    return response.json()

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(INFLUXDB_DATABASE)
    client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

token = get_access_token()
summary = get_daily_summary(token)

for day in summary['items']:
    for player in day['devicePlayers']:
        for playedApp in player['playedApps']:
            for app in day['playedApps']:
                if app['applicationId'] == playedApp['applicationId']:
                    points.append({
                            "measurement": "time",
                            "time": day['date'],
                            "tags": {
                                "player_id": player['playerId'],
                                "application_id": app['applicationId'],
                                "platform": "Nintendo Switch",
                                "player_name": player['nickname'],
                                "title": app['title'],
                            },
                            "fields": {
                                "value": playedApp['playingTime'],
                                "image": app['imageUri']['large'],
                                "url": app['shopUri']
                            }
                        })

try:
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))
