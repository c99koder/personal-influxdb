#!/usr/bin/python3

#  Copyright (C) 2022 Sam Steele
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

import requests, sys, pytz
from datetime import datetime, date, timedelta
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

LOCAL_TIMEZONE = pytz.timezone('America/New_York')
ONETOUCH_USERNAME = ''
ONETOUCH_PASSWORD = ''
ONETOUCH_URL = 'https://app.onetouchreveal.com'
STARTDATE = (date.today() - timedelta(days=date.today().weekday())).strftime("%Y-%m-%d %H:%M:%S")
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'glucose'
points = []

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(INFLUXDB_DATABASE)
    client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

try:
    response = requests.post(ONETOUCH_URL + '/mobile/user/v3/authenticate',
        headers={'Content-Type': 'application/json', 'login': ONETOUCH_USERNAME, 'password':ONETOUCH_PASSWORD})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print("HTTP request failed: %s" % (err))
    sys.exit()

data = response.json()
if not 'token' in data['result']:
    print("Authentication failed")
    sys.exit(1)

ONETOUCH_TOKEN = data['result']['token']
try:
    response = requests.post(ONETOUCH_URL + '/mobile/health/v1/data/subscribe',
        json={'endDate':'', 'lastSyncTime':0,'readingTypes':['bgReadings'], 'startDate':STARTDATE},
        headers={'Content-Type': 'application/json', 'authenticationtoken': ONETOUCH_TOKEN, 'token':ONETOUCH_TOKEN})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print("HTTP request failed: %s" % (err))
    sys.exit()

data = response.json()

if len(data['result']['bgReadings']) > 0:
    for reading in data['result']['bgReadings']:
        time = datetime.strptime(reading['readingDate'], "%Y-%m-%d %H:%M:%S")
        utc_time = LOCAL_TIMEZONE.localize(time).astimezone(pytz.utc).isoformat()
        points.append({
            "measurement": "glucose",
            "time": utc_time,
            "tags": {
                "deviceType": reading['deviceType'],
                "deviceSerialNumber": reading['deviceSerialNumber'],
            },
            "fields": {
                "value": reading['bgValue']['value'],
                "units": reading['bgValue']['units'],
            }
        })

try:
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))
