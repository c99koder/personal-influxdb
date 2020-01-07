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

import requests, sys
from datetime import datetime, date, timedelta
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

EXIST_ACCESS_TOKEN = ''
EXIST_USERNAME = ''
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'exist'
points = []

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

def fetch_attribute(attribute):
    try:
        response = requests.get('https://exist.io/api/1/users/' + EXIST_USERNAME + '/attributes/' + attribute + '/?limit=10',
            headers={'Authorization':'Bearer ' + EXIST_ACCESS_TOKEN})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("HTTP request failed: %s" % (err))
        sys.exit()
    data = response.json()
    print("Got %s %s values from exist.io" % (len(data['results']), attribute))

    for result in data['results']:
        if result['value'] != None:
            if attribute == 'custom':
                for tag in result['value'].split(', '):
                    if len(tag) > 0:
                        points.append({
                            "measurement": attribute,
                            "time": result['date'] + "T00:00:00",
                            "tags": {
                                "tag": tag
                            },
                            "fields": {
                                "value": tag
                            }
                        })
            else:
                points.append({
                    "measurement": attribute,
                    "time": result['date'] + "T00:00:00",
                    "fields": {
                        "value": result['value']
                    }
                })
    return data

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(INFLUXDB_DATABASE)
    client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

acquire_attributes([{"name":"gaming_min", "active":True}])

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
            "html": insight['html'],
            "text": insight['text']
        }
    })

fetch_attribute('custom')
fetch_attribute('mood')

try:
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))

values = []
tags = []
client.switch_database('fitbit')
totals = client.query('SELECT count("duration") AS "total" FROM "activity" WHERE activityName = \'Meditating\' AND time > now() - 7d GROUP BY time(1d) ORDER BY "time" DESC')
for total in list(totals.get_points()):
    if total['total'] > 0:
        date = datetime.fromisoformat(total['time'].strip('Z')).strftime('%Y-%m-%d')
        tags.append({'date': date, 'value': 'meditation'})

totals = client.query('SELECT count("duration") AS "total" FROM "activity" WHERE activityName != \'Meditating\' AND time > now() - 7d GROUP BY time(1d) ORDER BY "time" DESC')
for total in list(totals.get_points()):
    if total['total'] > 0:
        date = datetime.fromisoformat(total['time'].strip('Z')).strftime('%Y-%m-%d')
        tags.append({'date': date, 'value': 'exercise'})

client.switch_database('trakt')
totals = client.query('SELECT count("title") AS "total" FROM "watch" WHERE time > now() - 7d GROUP BY time(1d) ORDER BY "time" DESC')
for total in list(totals.get_points()):
    if total['total'] > 0:
        date = datetime.fromisoformat(total['time'].strip('Z')).strftime('%Y-%m-%d')
        tags.append({'date': date, 'value': 'tv'})

client.switch_database('gaming')
totals = client.query('SELECT sum("value") AS "total" FROM "time" WHERE "value" > 0 AND time > now() - 7d GROUP BY time(1d) ORDER BY "time" DESC')
for total in list(totals.get_points()):
    date = datetime.fromisoformat(total['time'].strip('Z')).strftime('%Y-%m-%d')
    if total['total'] != None and total['total'] > 0:
        values.append({'date': date, 'name': 'gaming_min', 'value': int(total['total'] / 60)})
        tags.append({'date': date, 'value': 'gaming'})
    else:
        values.append({'date': date, 'name': 'gaming_min', 'value': 0})

append_tags(tags)
post_attributes(values)
