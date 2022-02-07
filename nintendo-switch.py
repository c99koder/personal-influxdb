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
from config import *

if not NS_DEVICE_ID:
    logging.error("NS_DEVICE_ID not set in config.py")
    sys.exit(1)

GRANT_TYPE = 'urn:ietf:params:oauth:grant-type:jwt-bearer-session-token'
points = []


def get_access_token():
    response = requests.post('https://accounts.nintendo.com/connect/1.0.0/api/token', data={
        'session_token': NS_SESSION_TOKEN,
        'client_id': NS_CLIENT_ID,
        'grant_type': GRANT_TYPE
    })
    return response.json()


def get_daily_summary(access):
    response = requests.get(f'https://api-lp1.pctl.srv.nintendo.net/moon/v1/devices/{NS_DEVICE_ID}/daily_summaries', headers={
        'x-moon-os-language': 'en-US',
        'x-moon-app-language': 'en-US',
        'authorization': f"{access['token_type']} {access['access_token']}",
        'x-moon-app-internal-version': NS_INTERNAL_VERSION,
        'x-moon-app-display-version': NS_DISPLAY_VERSION,
        'x-moon-app-id': 'com.nintendo.znma',
        'x-moon-os': 'IOS',
        'x-moon-os-version': NS_OS_VERSION,
        'x-moon-model': 'iPhone11,8',
        'accept-encoding': 'gzip;q=1.0, compress;q=0.5',
        'accept-language': 'en-US;q=1.0',
        'user-agent': 'moon_ios/' + NS_DISPLAY_VERSION + ' (com.nintendo.znma; build:' + NS_INTERNAL_VERSION + '; iOS ' + NS_OS_VERSION + ') Alamofire/4.8.2',
        'x-moon-timezone': 'America/Los_Angeles',
        'x-moon-smart-device-id': NS_SMART_DEVICE_ID
    })
    return response.json()

def get_monthly_summary(month, access):
    response = requests.get(f'https://api-lp1.pctl.srv.nintendo.net/moon/v1/devices/{NS_DEVICE_ID}/monthly_summaries/{month}', headers={
        'x-moon-os-language': 'en-US',
        'x-moon-app-language': 'en-US',
        'authorization': f"{access['token_type']} {access['access_token']}",
        'x-moon-app-internal-version': NS_INTERNAL_VERSION,
        'x-moon-app-display-version': NS_DISPLAY_VERSION,
        'x-moon-app-id': 'com.nintendo.znma',
        'x-moon-os': 'IOS',
        'x-moon-os-version': NS_OS_VERSION,
        'x-moon-model': 'iPhone11,8',
        'accept-encoding': 'gzip;q=1.0, compress;q=0.5',
        'accept-language': 'en-US;q=1.0',
        'user-agent': 'moon_ios/' + NS_DISPLAY_VERSION + ' (com.nintendo.znma; build:' + NS_INTERNAL_VERSION + '; iOS ' + NS_OS_VERSION + ') Alamofire/4.8.2',
        'x-moon-timezone': 'America/Los_Angeles',
        'x-moon-smart-device-id': NS_SMART_DEVICE_ID
    })
    return response.json()

connect(NS_DATABASE)
token = get_access_token()
summary = get_daily_summary(token)

for day in summary['items']:
    for player in day['devicePlayers']:
        for playedApp in player['playedApps']:
            for app in day['playedApps']:
                if app['applicationId'] == playedApp['applicationId']:
                    points.append({
                            "measurement": "time",
                            "time": day['date'],
                            "tags": {
                                "player_id": player['playerId'],
                                "application_id": app['applicationId'],
                                "platform": "Nintendo Switch",
                                "player_name": player['nickname'],
                                "title": app['title'],
                            },
                            "fields": {
                                "value": playedApp['playingTime'],
                                "image": app['imageUri']['large'],
                                "url": app['shopUri']
                            }
                        })

write_points(points)
