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

import requests, sys, os, pytz
from datetime import datetime, date, timedelta
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

LOCAL_TIMEZONE = pytz.timezone('America/New_York')
FITBIT_LANGUAGE = 'en_US'
FITBIT_CLIENT_ID = ''
FITBIT_CLIENT_SECRET = ''
FITBIT_ACCESS_TOKEN = ''
FITBIT_INITIAL_CODE = ''
REDIRECT_URI = 'https://localhost'
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'fitbit'
points = []

def fetch_data(category, type):
    try:
        response = requests.get('https://api.fitbit.com/1/user/-/' + category + '/' + type + '/date/today/1d.json', 
            headers={'Authorization': 'Bearer ' + FITBIT_ACCESS_TOKEN, 'Accept-Language': FITBIT_LANGUAGE})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("HTTP request failed: %s" % (err))
        sys.exit()

    data = response.json()
    print("Got " + type + " from Fitbit")

    for day in data[category + '-' + type]:
        points.append({
                "measurement": type,
                "time": datetime.fromisoformat(day['dateTime']),
                "fields": {
                    "value": float(day['value'])
                }
            })

def fetch_heartrate(date):
    try:
        response = requests.get('https://api.fitbit.com/1/user/-/activities/heart/date/' + date + '/1d/1min.json', 
            headers={'Authorization': 'Bearer ' + FITBIT_ACCESS_TOKEN, 'Accept-Language': FITBIT_LANGUAGE})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("HTTP request failed: %s" % (err))
        sys.exit()

    data = response.json()
    print("Got heartrates from Fitbit")

    for day in data['activities-heart']:
        if 'restingHeartRate' in day['value']:
            points.append({
                    "measurement": "restingHeartRate",
                    "time": datetime.fromisoformat(day['dateTime']),
                    "fields": {
                        "value": float(day['value']['restingHeartRate'])
                    }
                })

        if 'heartRateZones' in day['value']:
            for zone in day['value']['heartRateZones']:
                points.append({
                        "measurement": "heartRateZones",
                        "time": datetime.fromisoformat(day['dateTime']),
                        "tags": {
                            "zone": zone['name']
                        },
                        "fields": {
                            "caloriesOut": float(zone['caloriesOut']),
                            "min": float(zone['min']),
                            "max": float(zone['max']),
                            "minutes": float(zone['minutes'])
                        }
                    })

    if 'activities-heart-intraday' in data:
        for value in data['activities-heart-intraday']['dataset']:
            time = datetime.fromisoformat(date + "T" + value['time'])
            utc_time = LOCAL_TIMEZONE.localize(time).astimezone(pytz.utc).isoformat()
            points.append({
                    "measurement": "heartrate",
                    "time": utc_time,
                    "fields": {
                        "value": float(value['value'])
                    }
                })

def process_levels(levels):
    for level in levels:
        type = level['level']
        if type == "asleep":
            type = "light"
        if type == "restless":
            type = "rem"
        if type == "awake":
            type = "wake"

        time = datetime.fromisoformat(level['dateTime'])
        utc_time = LOCAL_TIMEZONE.localize(time).astimezone(pytz.utc).isoformat()
        points.append({
                "measurement": "sleep_levels",
                "time": utc_time,
                "fields": {
                    "seconds": int(level['seconds'])
                }
            })

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(INFLUXDB_DATABASE)
    client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

if not FITBIT_ACCESS_TOKEN:
    if os.path.isfile('.fitbit-refreshtoken'):
        f = open(".fitbit-refreshtoken", "r")
        token = f.read();
        f.close();
        response = requests.post('https://api.fitbit.com/oauth2/token',
            data={
                "client_id": FITBIT_CLIENT_ID,
                "grant_type": "refresh_token",
                "redirect_uri": REDIRECT_URI,
                "refresh_token": token
            }, auth=(FITBIT_CLIENT_ID, FITBIT_CLIENT_SECRET))
    else:
        response = requests.post('https://api.fitbit.com/oauth2/token',
            data={
                "client_id": FITBIT_CLIENT_ID,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
                "code": FITBIT_INITIAL_CODE
            }, auth=(FITBIT_CLIENT_ID, FITBIT_CLIENT_SECRET))

    response.raise_for_status();

    json = response.json()
    FITBIT_ACCESS_TOKEN = json['access_token']
    refresh_token = json['refresh_token']
    f = open(".fitbit-refreshtoken", "w+")
    f.write(refresh_token)
    f.close()

end = date.today()
start = end - timedelta(days=1)

try:
    response = requests.get('https://api.fitbit.com/1.2/user/-/sleep/date/' + start.isoformat() + '/' + end.isoformat() + '.json',
        headers={'Authorization': 'Bearer ' + FITBIT_ACCESS_TOKEN, 'Accept-Language': FITBIT_LANGUAGE})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print("HTTP request failed: %s" % (err))
    sys.exit()

data = response.json()
print("Got sleep sessions from Fitbit")

for day in data['sleep']:
    time = datetime.fromisoformat(day['startTime'])
    utc_time = LOCAL_TIMEZONE.localize(time).astimezone(pytz.utc).isoformat()
    if day['type'] == 'stages':
        points.append({
            "measurement": "sleep",
            "time": utc_time,
            "fields": {
                "duration": int(day['duration']),
                "efficiency": int(day['efficiency']),
                "is_main_sleep": bool(day['isMainSleep']),
                "minutes_asleep": int(day['minutesAsleep']),
                "minutes_awake": int(day['minutesAwake']),
                "time_in_bed": int(day['timeInBed']),
                "minutes_deep": int(day['levels']['summary']['deep']['minutes']),
                "minutes_light": int(day['levels']['summary']['light']['minutes']),
                "minutes_rem": int(day['levels']['summary']['rem']['minutes']),
                "minutes_wake": int(day['levels']['summary']['wake']['minutes']),
            }
        })
    else:
        points.append({
            "measurement": "sleep",
            "time": utc_time,
            "fields": {
                "duration": int(day['duration']),
                "efficiency": int(day['efficiency']),
                "is_main_sleep": bool(day['isMainSleep']),
                "minutes_asleep": int(day['minutesAsleep']),
                "minutes_awake": int(day['minutesAwake']),
                "time_in_bed": int(day['timeInBed']),
                "minutes_deep": 0,
                "minutes_light": int(day['levels']['summary']['asleep']['minutes']),
                "minutes_rem": int(day['levels']['summary']['restless']['minutes']),
                "minutes_wake": int(day['levels']['summary']['awake']['minutes']),
            }
        })
    
    if 'data' in day['levels']:
        process_levels(day['levels']['data'])
    
    if 'shortData' in day['levels']:
        process_levels(day['levels']['shortData'])

fetch_data('activities', 'steps')
fetch_data('activities', 'distance')
fetch_data('activities', 'floors')
fetch_data('activities', 'elevation')
fetch_data('activities', 'distance')
fetch_data('activities', 'minutesSedentary')
fetch_data('activities', 'minutesLightlyActive')
fetch_data('activities', 'minutesFairlyActive')
fetch_data('activities', 'minutesVeryActive')
fetch_data('activities', 'calories')
fetch_data('activities', 'activityCalories')
fetch_data('body', 'weight')
fetch_data('body', 'fat')
fetch_data('body', 'bmi')
fetch_heartrate(date.today().isoformat())

try:
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))
