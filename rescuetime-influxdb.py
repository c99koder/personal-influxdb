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

import requests, pytz, sys
from datetime import datetime
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

LOCAL_TIMEZONE = pytz.timezone('America/New_York')
RESCUETIME_API_KEY = '' #Create a key here: https://www.rescuetime.com/anapi/manage
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'rescuetime'

try:
	client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
	client.create_database(INFLUXDB_DATABASE)
	client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
	print("InfluxDB connection failed: %s" % (err))
	sys.exit()

try:
	response = requests.get('https://www.rescuetime.com/anapi/data',
		params={"key":RESCUETIME_API_KEY, "perspective":"interval", "restrict_kind":"activity", "format":"json"})
	response.raise_for_status()
except requests.exceptions.HTTPError as err:
	print("HTTP request failed: %s" % (err))
	sys.exit()

activities = response.json()
print("Got %s activites from RescueTime" % len(activities['rows']))
points = []

for activity in activities['rows']:
	time = datetime.fromisoformat(activity[0])
	utc_time = LOCAL_TIMEZONE.localize(time).astimezone(pytz.utc).isoformat()
	points.append({
			"measurement": "activity",
			"time": utc_time,
			"tags": {
				"activity": activity[3],
				"category": activity[4]
			},
			"fields": {
				"duration": activity[1],
				"productivity": activity[5],
			}
		})

try:
	time = datetime.fromisoformat(activities['rows'][0][0])
	utc_time = LOCAL_TIMEZONE.localize(time).astimezone(pytz.utc).isoformat()
	client.query("DELETE WHERE time >= $start", bind_params={"start": utc_time});
	client.write_points(points)
except InfluxDBClientError as err:
	print("Unable to write points to InfluxDB: %s" % (err))
	sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))