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
EXIST_ACCESS_TOKEN = ''
EXIST_USERNAME = ''
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'exist'
FITBIT_DATABASE = 'fitbit'
TRAKT_DATABASE = 'trakt'
GAMING_DATABASE = 'gaming'
points = []
start_time = str(int(LOCAL_TIMEZONE.localize(datetime.combine(date.today(), time(0,0)) - timedelta(days=7)).astimezone(pytz.utc).timestamp()) * 1000) + 'ms'

def append_tags(tags):
    try:
        response = requests.post('https://exist.io/api/1/attributes/custom/append/',
            headers={'Authorization':'Bearer ' + EXIST_ACCESS_TOKEN},
            json=tags)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("HTTP request failed: %s" % (err))
        sys.exit()

    result = response.json()
    if len(result['failed']) > 0:
        print("Request failed: %s" % result['failed'])
        sys.exit()

    if len(result['success']) > 0:
        print("Successfully sent %s tags" % len(result['success']))

def acquire_attributes(attributes):
    try:
        response = requests.post('https://exist.io/api/1/attributes/acquire/',
            headers={'Authorization':'Bearer ' + EXIST_ACCESS_TOKEN},
            json=attributes)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("HTTP request failed: %s" % (err))
        sys.exit()

    result = response.json()
    if len(result['failed']) > 0:
        print("Request failed: %s" % result['failed'])
        sys.exit()

def post_attributes(values):
    try:
        response = requests.post('https://exist.io/api/1/attributes/update/',
            headers={'Authorization':'Bearer ' + EXIST_ACCESS_TOKEN},
            json=values)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("HTTP request failed: %s" % (err))
        sys.exit()

    result = response.json()
    if len(result['failed']) > 0:
        print("Request failed: %s" % result['failed'])
        sys.exit()

    if len(result['success']) > 0:
        print("Successfully sent %s attributes" % len(result['success']))

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(INFLUXDB_DATABASE)
    client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

acquire_attributes([{"name":"gaming_min", "active":True}, {"name":"tv_min", "active":True}])

try:
    response = requests.get('https://exist.io/api/1/users/' + EXIST_USERNAME + '/insights/',
        headers={'Authorization':'Bearer ' + EXIST_ACCESS_TOKEN})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print("HTTP request failed: %s" % (err))
    sys.exit()

data = response.json()
print("Got %s insights from exist.io" % len(data['results']))

for insight in data['results']:
    if insight['target_date'] == None:
        date = datetime.fromisoformat(insight['created'].strip('Z')).strftime('%Y-%m-%d')
    else:
        date = insight['target_date']
    points.append({
        "measurement": "insight",
        "time": date + "T00:00:00",
        "tags": {
            "type": insight['type']['name'],
            "attribute": insight['type']['attribute']['label'],
            "group": insight['type']['attribute']['group']['label'],
        },
        "fields": {
            "html": insight['html'].replace("\n", "").replace("\r", ""),
            "text": insight['text']
        }
    })

try:
    response = requests.get('https://exist.io/api/1/users/' + EXIST_USERNAME + '/attributes/?limit=7&groups=custom,mood',
        headers={'Authorization':'Bearer ' + EXIST_ACCESS_TOKEN})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print("HTTP request failed: %s" % (err))
    sys.exit()

data = response.json()
print("Got attributes from exist.io")

for result in data:
    for value in result['values']:
        if value['value'] != None and value['value'] != '' and result['attribute'] != 'custom':
            if result['group']['name'] == 'custom':
                points.append({
                    "measurement": result['group']['name'],
                    "time": value['date'] + "T00:00:00",
                    "tags": {
                        "tag": result['label']
                    },
                    "fields": {
                        "value": value['value']
                    }
                })
            else:
                points.append({
                    "measurement": result['group']['name'],
                    "time": value['date'] + "T00:00:00",
                    "fields": {
                        "value": value['value']
                    }
                })

try:
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))

values = []
tags = []
client.switch_database(FITBIT_DATABASE)
durations = client.query('SELECT "duration" FROM "activity" WHERE activityName = \'Meditating\' AND time >= ' + start_time)
for duration in list(durations.get_points()):
    if duration['duration'] > 0:
        date = datetime.fromisoformat(duration['time'].strip('Z') + "+00:00").astimezone(LOCAL_TIMEZONE).strftime('%Y-%m-%d')
        tags.append({'date': date, 'value': 'meditation'})

durations = client.query('SELECT "duration" FROM "activity" WHERE activityName != \'Meditating\' AND time >= ' + start_time)
for duration in list(durations.get_points()):
    if duration['duration'] > 0:
        date = datetime.fromisoformat(duration['time'].strip('Z') + "+00:00").astimezone(LOCAL_TIMEZONE).strftime('%Y-%m-%d')
        tags.append({'date': date, 'value': 'exercise'})

totals = {}
client.switch_database(TRAKT_DATABASE)
durations = client.query('SELECT "duration" FROM "watch" WHERE time >= ' + start_time)
for duration in list(durations.get_points()):
    date = datetime.fromisoformat(duration['time'].strip('Z') + "+00:00").astimezone(LOCAL_TIMEZONE).strftime('%Y-%m-%d')
    if date in totals:
        totals[date] = totals[date] + duration['duration']
    else:
        totals[date] = duration['duration']

for date in totals:
    values.append({'date': date, 'name': 'tv_min', 'value': int(totals[date])})
    tags.append({'date': date, 'value': 'tv'})

totals = {}
client.switch_database(GAMING_DATABASE)
durations = client.query('SELECT "value" FROM "time" WHERE "value" > 0 AND time >= ' + start_time)
for duration in list(durations.get_points()):
    date = datetime.fromisoformat(duration['time'].strip('Z') + "+00:00").astimezone(LOCAL_TIMEZONE).strftime('%Y-%m-%d')
    if date in totals:
        totals[date] = totals[date] + duration['value']
    else:
        totals[date] = duration['value']

for date in totals:
    values.append({'date': date, 'name': 'gaming_min', 'value': int(totals[date] / 60)})
    tags.append({'date': date, 'value': 'gaming'})

append_tags(tags)
post_attributes(values)
