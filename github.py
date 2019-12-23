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
from datetime import datetime
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

GITHUB_API_KEY = ''
GITHUB_USERNAME = ''
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'github'

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(INFLUXDB_DATABASE)
    client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

try:
    response = requests.get('https://api.github.com/user/repos',
        params={'sort': 'pushed', 'per_page':10},
        headers={'Authorization': 'token ' + GITHUB_API_KEY, 'User-Agent': GITHUB_USERNAME})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print("HTTP request failed: %s" % (err))
    sys.exit()

repos = response.json()
print("Got %s repos from GitHub" % len(repos))
if len(repos) == 0:
    sys.exit()

points = []

for repo in repos:
    print("Fetch statistics for " + repo['full_name'])
    try:
        response = requests.get(repo['url'] + '/stats/contributors',
            params={'sort': 'pushed'},
            headers={'Authorization': 'token ' + GITHUB_API_KEY, 'User-Agent': GITHUB_USERNAME})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("HTTP request failed: %s" % (err))
        sys.exit()

    contributors = response.json()
    for contributor in contributors:
        if contributor['author']['login'] == GITHUB_USERNAME:
            for week in contributor['weeks']:
                if week['c'] > 0:
                    points.append({
                        "measurement": "commits",
                        "time": datetime.fromtimestamp(week['w']).isoformat(),
                        "tags": {
                            "username": GITHUB_USERNAME,
                            "repo": repo['full_name']
                        },
                        "fields": {
                            "value": week['c']
                        }
                    })

try:
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))
