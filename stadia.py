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
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from config import *

if not EXOPHASE_NAME:
    logging.error("EXOPHASE_NAME not set in config.py")
    sys.exit(1)

points = []

def scrape_exophase_id():
    try:
        response = requests.get(f"https://www.exophase.com/user/{EXOPHASE_NAME}")
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error("HTTP request failed: %s", err)
        sys.exit(1)
    soup = BeautifulSoup(response.text, 'html.parser')
    return [soup.find("a", attrs={'data-playerid': True})['data-playerid'], soup.find("div", attrs={'data-userid': True})['data-userid']]

def scrape_latest_games(platform):
    games = []
    try:
        response = requests.get(f"https://www.exophase.com/{platform}/user/{EXOPHASE_NAME}")
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error("HTTP request failed: %s", err)
        sys.exit(1)
    soup = BeautifulSoup(response.text, 'html.parser')
    for game in soup.find_all("li", attrs={'data-gameid': True}):
        playtime = int(float(game.select_one("span.hours").get_text()[:-1]) * 60)
        img = game.select_one("div.image > img")['src']
        img = urljoin(img, urlparse(img).path).replace("/games/m/", "/games/l/")
        games.append({'gameid': game['data-gameid'],
        'time': datetime.fromtimestamp(float(game['data-lastplayed'])),
        'title': game.select_one("h3 > a").string,
        'url': game.select_one("h3 > a")['href'],
        'image': img,
        'playtime': playtime,
        })

    return games

def scrape_achievements(url, gameid):
    achievements = []
    try:
        response = requests.get(f"https://api.exophase.com/public/player/{urlparse(url).fragment}/game/{gameid}/earned")
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error("HTTP request failed: %s", err)
        sys.exit(1)
    api_data = response.json()
    if api_data['success'] == True:
        achievement_data = {}
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        for achievement in soup.find_all("li", attrs={'data-type': 'achievement'}):
            img = achievement.select_one("div.image > img")['src']
            img = urljoin(img, urlparse(img).path)
            achievement_data[achievement['id']] = {'id': achievement['id'],
            'name': achievement.select_one("div.award-title > a").string.replace("\xa0", " "),
            'description': achievement.select_one("div.award-description > p").string.replace("\xa0", " "),
            'image': img
            }

        for achievement in api_data['list']:
            data = achievement_data[str(achievement['awardid'])]
            data['time'] = datetime.fromtimestamp(achievement['timestamp'])
            achievements.append(data)

    return achievements

client = connect(STADIA_DATABASE)

PLAYERID, USERID = scrape_exophase_id()
totals = client.query(f'SELECT last("total") AS "total" FROM "time" WHERE "platform" = \'Stadia\' AND "total" > 0 AND "player_id" = \'{PLAYERID}\' GROUP BY "application_id" ORDER BY "time" DESC')

for game in scrape_latest_games('stadia'):
    value = game['playtime']
    total = list(totals.get_points(tags={'application_id': str(game['gameid'])}))
    if len(total) == 1 and total[0]['total'] > 0:
        value = game['playtime'] - total[0]['total']
    if value > 1:
        points.append({
            "measurement": "time",
            "time": game['time'].isoformat(),
            "tags": {
                "player_id": PLAYERID,
                "application_id": game['gameid'],
                "platform": "Stadia",
                "player_name": STADIA_NAME,
                "title": game['title'],
            },
            "fields": {
                "value": int(value) * 60,
                "total": game['playtime'],
                "image": game['image'],
                "url": game['url']
            }
        })

    for achievement in scrape_achievements(game['url'], game['gameid']):
        points.append({
                "measurement": "achievement",
                "time": achievement['time'].isoformat(),
                "tags": {
                    "player_id": PLAYERID,
                    "application_id": game['gameid'],
                    "apiname":achievement['id'],
                    "platform": "Stadia",
                    "player_name": STADIA_NAME,
                    "title": game['title'],
                },
                "fields": {
                    "name": achievement['name'],
                    "description": achievement['description'],
                    "icon": achievement['image'],
                    "icon_gray": achievement['image'],
                }
            })

write_points(points)
