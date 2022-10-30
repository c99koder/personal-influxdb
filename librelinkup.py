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

import requests, sys
from datetime import datetime, date, timedelta
from config import *

def append_reading(points, data, reading):
    time = datetime.strptime(reading['FactoryTimestamp'] + '+00:00', '%m/%d/%Y %I:%M:%S %p%z')
    points.append({
        "measurement": "glucose",
        "time": time,
        "tags": {
            "deviceType": "Libre",
            "deviceSerialNumber": data['data']['connection']['sensor']['sn'],
        },
        "fields": {
            "value": int(reading['ValueInMgPerDl']),
            "units": 'mg/dL',
        }
    })

if not LIBRELINKUP_USERNAME:
    logging.error("LIBRELINKUP_USERNAME not set in config.py")
    sys.exit(1)

STARTDATE = (date.today() - timedelta(days=date.today().weekday())).strftime("%Y-%m-%d %H:%M:%S")
points = []

connect(LIBRELINKUP_DATABASE)

libreLinkUpHttpHeaders = {
    "version": LIBRELINKUP_VERSION,
    "product": LIBRELINKUP_PRODUCT,
}

try:
    response = requests.post(f'{LIBRELINKUP_URL}/llu/auth/login',
        headers=libreLinkUpHttpHeaders, json = {'email': LIBRELINKUP_USERNAME, 'password': LIBRELINKUP_PASSWORD})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    logging.error("HTTP request failed: %s", err)
    sys.exit(1)

data = response.json()
if not 'authTicket' in data['data']:
    logging.error("Authentication failed")
    sys.exit(1)

LIBRELINKUP_TOKEN = data['data']['authTicket']['token']
libreLinkUpHttpHeaders['Authorization'] = 'Bearer ' + LIBRELINKUP_TOKEN

try:
    response = requests.get(f'{LIBRELINKUP_URL}/llu/connections', headers=libreLinkUpHttpHeaders)
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    logging.error("HTTP request failed: %s", err)
    sys.exit(1)

connections = response.json()
if not 'data' in connections or len(connections['data']) < 1:
    logging.error("No connections configured. Accept an invitation in the mobile app first.")
    sys.exit(1)

logging.info("Using connection %s: %s %s", connections['data'][0]['patientId'], connections['data'][0]['firstName'], connections['data'][0]['lastName'])

try:
    response = requests.get(f'{LIBRELINKUP_URL}/llu/connections/{connections["data"][0]["patientId"]}/graph', headers=libreLinkUpHttpHeaders)
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    logging.error("HTTP request failed: %s", err)
    sys.exit(1)

data = response.json()
append_reading(points, data, data['data']['connection']['glucoseMeasurement'])

if len(data['data']['graphData']) > 0:
    for reading in data['data']['graphData']:
        append_reading(points, data, reading)

write_points(points)

