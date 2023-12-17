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

import requests, sys, os, json, time
from datetime import datetime
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

points = []

connect(LIBRELINKUP_DATABASE)

LIBRELINKUP_HEADERS = {
    "version": LIBRELINKUP_VERSION,
    "product": LIBRELINKUP_PRODUCT,
}

LIBRELINKUP_TOKEN = None
script_dir = os.path.dirname(__file__)
auth_token_path = os.path.join(script_dir, '.librelinkup-authtoken')
if os.path.isfile(auth_token_path):
    with open(auth_token_path) as json_file:
            auth = json.load(json_file)
            if auth['expires'] > time.time():
                LIBRELINKUP_TOKEN = auth['token']
                logging.info("Using cached authTicket, expiration: %s", datetime.fromtimestamp(auth['expires']).isoformat())

if LIBRELINKUP_TOKEN is None:
    logging.info("Auth ticket not found or expired, requesting a new one")
    try:
        response = requests.post(f'{LIBRELINKUP_URL}/llu/auth/login',
            headers=LIBRELINKUP_HEADERS, json = {'email': LIBRELINKUP_USERNAME, 'password': LIBRELINKUP_PASSWORD})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error("HTTP request failed: %s", err)
        sys.exit(1)

    data = response.json()
    if not 'authTicket' in data['data']:
        logging.error("Authentication failed. Server response:")
        logging.info(data)
        if 'redirect' in data['data'] and data['data']['redirect'] is True:
            region = data['data']['region']
            logging.error(f"The LibreLinkUp API returned a redirect. You should try the following url for LIBRELINKUP_URL in config.py: https://api-{region}.libreview.io")
        sys.exit(1)

    with open(auth_token_path, 'w') as outfile:
        json.dump(data['data']['authTicket'], outfile)

    LIBRELINKUP_TOKEN = data['data']['authTicket']['token']

LIBRELINKUP_HEADERS['Authorization'] = 'Bearer ' + LIBRELINKUP_TOKEN

try:
    response = requests.get(f'{LIBRELINKUP_URL}/llu/connections', headers=LIBRELINKUP_HEADERS)
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
    response = requests.get(f'{LIBRELINKUP_URL}/llu/connections/{connections["data"][0]["patientId"]}/graph', headers=LIBRELINKUP_HEADERS)
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
