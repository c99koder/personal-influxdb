#!/usr/bin/python3
# Copyright 2023 Sam Steele
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

import requests, sys, re, json
from datetime import datetime
from config import *

if not STEAM_API_KEY:
    logging.error("STEAM_API_KEY not set in config.py")
    sys.exit(1)

points = []

def fetch_schema(appId):
    try:
        response = requests.get('https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v1/', 
            params={'key': STEAM_API_KEY, 'steamid': STEAM_ID, 'appid': appId, 'l': STEAM_LANGUAGE})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error("HTTP request failed: %s", err)
        sys.exit(1)
    json = response.json()
    if 'game' in json:
        return json['game']
    else:
        return {}

def fetch_achievements(appId):
    try:
        response = requests.get('https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/', 
            params={'key': STEAM_API_KEY, 'steamid': STEAM_ID, 'appid': appId})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error("HTTP request failed: %s", err)
        sys.exit(1)
    json = response.json()
    if 'playerstats' in json and 'achievements' in json['playerstats']:
        logging.info("Got %s achievements from Steam for appId %s", len(json['playerstats']['achievements']), appId)
        return json['playerstats']['achievements']
    else:
        return []

def fetch_recents():
    try:
        response = requests.get('https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/',
            params={'key': STEAM_API_KEY, 'steamid': STEAM_ID})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error("HTTP request failed: %s", err)
        sys.exit(1)
    json = response.json()
    if 'response' in json and 'games' in json['response']:
        logging.info("Got %s games from Steam recents", json['response']['total_count'])
        return json['response']['games']
    else:
        return []

def fetch_owned_games():
    try:
        response = requests.get('https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/',
            params={'key': STEAM_API_KEY, 'steamid': STEAM_ID})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error("HTTP request failed: %s", err)
        sys.exit(1)
    json = response.json()
    if 'response' in json and 'games' in json['response']:
        logging.info("Got %s games from Steam library", json['response']['game_count'])
        return json['response']['games']
    else:
        return []

client = connect(STEAM_DATABASE)

totals = client.query(f'SELECT last("total") AS "total" FROM "time" WHERE "platform" = \'Steam\' AND "total" > 0 AND "player_id" = \'{STEAM_ID}\' GROUP BY "application_id" ORDER BY "time" DESC')
games = fetch_owned_games()

for app in fetch_recents():
    for game in games:
        if game['appid'] == app['appid']:
            value = app['playtime_2weeks']
            total = list(totals.get_points(tags={'application_id': str(app['appid'])}))
            if len(total) == 1 and total[0]['total'] > 0:
                value = app['playtime_forever'] - total[0]['total']
            if value > 1:
                points.append({
                    "measurement": "time",
                    "time": datetime.fromtimestamp(game['rtime_last_played']).isoformat(),
                    "tags": {
                        "player_id": STEAM_ID,
                        "application_id": app['appid'],
                        "platform": "Steam",
                        "player_name": STEAM_USERNAME,
                        "title": app['name'],
                    },
                    "fields": {
                        "value": int(value) * 60,
                        "total": app['playtime_forever'],
                        "image": f"https://steamcdn-a.akamaihd.net/steam/apps/{app['appid']}/header.jpg",
                        "url": f"https://store.steampowered.com/app/{app['appid']}/"
                    }
                })

            schema = fetch_schema(app['appid'])
            if 'availableGameStats' in schema and 'achievements' in schema['availableGameStats']:
                achievements = schema['availableGameStats']['achievements']
                for achievement in fetch_achievements(app['appid']):
                    if achievement['unlocktime'] > 0:
                        description = None
                        if 'description' in achievements[achievement['apiname']]:
                            description = achievements[achievement['apiname']]['description']

                        points.append({
                                "measurement": "achievement",
                                "time": datetime.fromtimestamp(achievement['unlocktime']).isoformat(),
                                "tags": {
                                    "player_id": STEAM_ID,
                                    "application_id": app['appid'],
                                    "apiname":achievement['apiname'],
                                    "platform": "Steam",
                                    "player_name": STEAM_USERNAME,
                                    "title": app['name'],
                                },
                                "fields": {
                                    "name": achievements[achievement['apiname']]['displayName'],
                                    "description": description,
                                    "icon": achievements[achievement['apiname']]['icon'],
                                    "icon_gray": achievements[achievement['apiname']]['icongray'],
                                }
                            })

write_points(points)
