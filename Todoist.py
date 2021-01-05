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
from todoist.api import TodoistAPI

TODOIST_ACCESS_TOKEN = ''
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'todoist'
points = []

def get_activity(page):
	events = []
	count = -1
	offset = 0	
	while count == -1 or len(events) < count:
		print("Fetching page %s offset %s" % (page, len(events)))
		activity = api.activity.get(page=page, offset=len(events), limit=100)
		events.extend(activity['events'])
		count = activity['count']

	print("Got %s items from Todoist" % len(events))

	return events

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(INFLUXDB_DATABASE)
    client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

api = TodoistAPI(TODOIST_ACCESS_TOKEN)
api.sync()

page = 0
activity = get_activity(page)
projects = {}
for event in activity:
	if event['object_type'] == 'item':
		if event['event_type'] == 'added' or event['event_type'] == 'completed':
			project = None
			try:
				if event['parent_project_id'] in projects:
					project = projects[event['parent_project_id']]
				else:
					project = api.projects.get(event['parent_project_id'])
					projects[event['parent_project_id']] = project
			except AttributeError as err:
				print("Unable to fetch name for project ID %s" % event['parent_project_id'])

			if project != None:
				points.append({
			            "measurement": event['event_type'],
			            "time": event['event_date'],
			            "tags": {
			                "item_id": event['id'],
			                "project_id": event['parent_project_id'],
			                "project_name": project['project']['name'],
			            },
			            "fields": {
			                "content": event['extra_data']['content']
			            }
			        })

try:
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))
