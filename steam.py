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

import requests, sys, re, json
from datetime import datetime, date, timedelta
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from bs4 import BeautifulSoup

STEAM_API_KEY = ''
STEAM_ID = ''
STEAM_USERNAME = ''
STEAM_LANGUAGE = 'en'
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'gaming'
points = []

def fetch_schema(appId):
    response = requests.get('https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v1/', 
        params={'key': STEAM_API_KEY, 'steamid': STEAM_ID, 'appid': appId, 'l': STEAM_LANGUAGE})
    json = response.json()
    if 'game' in json:
        return json['game']
    else:
        return {}

def fetch_achievements(appId):
    response = requests.get('https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/', 
        params={'key': STEAM_API_KEY, 'steamid': STEAM_ID, 'appid': appId})
    json = response.json()
    if 'playerstats' in json and 'achievements' in json['playerstats']:
        print("Got %s achievements from Steam for appId %s" % (len(json['playerstats']['achievements']), appId))
        return json['playerstats']['achievements']
    else:
        return []

def fetch_recents():
    response = requests.get('https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/',
        params={'key': STEAM_API_KEY, 'steamid': STEAM_ID})
    json = response.json()
    if 'response' in json and 'games' in json['response']:
        print("Got %s games from Steam" % (json['response']['total_count']))
        return json['response']['games']
    else:
        return []

def scrape_recents():
    response = requests.get('https://steamcommunity.com/id/' + STEAM_USERNAME + '/games/?tab=all')
    soup = BeautifulSoup(response.text, 'html.parser')
    data = soup.find('script', string=re.compile('var rgGames = \[\{')).string
    return json.loads(data[data.index('['):data.index('}}];') + 3])

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(INFLUXDB_DATABASE)
    client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

totals = client.query('SELECT last("total") AS "total" FROM "time" WHERE "platform" = \'Steam\' AND "total" > 0 GROUP BY "application_id" ORDER BY "time" DESC')
recents = scrape_recents()

for app in fetch_recents():
    for recent in recents:
        if recent['appid'] == app['appid']:
            value = app['playtime_2weeks'];
            total = list(totals.get_points(tags={'application_id': str(app['appid'])}));
            if len(total) == 1 and total[0]['total'] > 0:
                value = app['playtime_forever'] - total[0]['total']
            if value > 1:
                points.append({
                    "measurement": "time",
                    "time": datetime.fromtimestamp(recent['last_played']).isoformat(),
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
                        "image": 'https://steamcdn-a.akamaihd.net/steam/apps/' + str(app['appid']) + '/header.jpg',
                        "url": 'https://store.steampowered.com/app/' + str(app['appid']) + '/'
                    }
                })

            schema = fetch_schema(app['appid'])
            if 'availableGameStats' in schema and 'achievements' in schema['availableGameStats']:
                achievements = schema['availableGameStats']['achievements'];
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

try:
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))
