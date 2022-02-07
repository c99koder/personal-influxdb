#!/usr/bin/python3
# Copyright 2022 Sam Steele
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests, sys, pytz
from datetime import datetime, date, timedelta
from config import *

if not ONETOUCH_USERNAME:
    logging.error("ONETOUCH_USERNAME not set in config.py")
    sys.exit(1)

STARTDATE = (date.today() - timedelta(days=date.today().weekday())).strftime("%Y-%m-%d %H:%M:%S")
points = []

connect(ONETOUCH_DATABASE)

try:
    response = requests.post(f'{ONETOUCH_URL}/mobile/user/v3/authenticate',
        headers={'Content-Type': 'application/json', 'login': ONETOUCH_USERNAME, 'password':ONETOUCH_PASSWORD})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    logging.error("HTTP request failed: %s", err)
    sys.exit(1)

data = response.json()
if not 'token' in data['result']:
    logging.error("Authentication failed")
    sys.exit(1)

ONETOUCH_TOKEN = data['result']['token']
try:
    response = requests.post(f'{ONETOUCH_URL}/mobile/health/v1/data/subscribe',
        json={'endDate':'', 'lastSyncTime':0,'readingTypes':['bgReadings'], 'startDate':STARTDATE},
        headers={'Content-Type': 'application/json', 'authenticationtoken': ONETOUCH_TOKEN, 'token':ONETOUCH_TOKEN})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    logging.error("HTTP request failed: %s", err)
    sys.exit(1)

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
                "value": int(reading['bgValue']['value']),
                "units": reading['bgValue']['units'],
            }
        })

write_points(points)
