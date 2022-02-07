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

import sys, os
from bs4 import BeautifulSoup
from config import *

points = []

def parse_activity(game):
    file = open(f'Takeout/Google Play Games Services/Games/{game}/Activity.html')
    html = BeautifulSoup(file, 'html.parser')
    file.close()

    for row in html.find_all('tr'):
        if row.contents[0].name == 'td' and row.contents[0].string == 'Time Last Played':
            points.append({
                    "measurement": "time",
                    "time": row.contents[1].string,
                    "tags": {
                        "platform": "Google Play",
                        "title": game,
                    },
                    "fields": {
                        "value": 0
                    }
                })

def parse_achievements(game):
    file = open(f'Takeout/Google Play Games Services/Games/{game}/Experience.html')
    html = BeautifulSoup(file, 'html.parser')
    file.close()

    for row in html.find_all('tr'):
        if row.contents[0].name == 'td' and row.contents[0].string == 'Achievement unlocked':
            date = row.contents[2].string
            game = row.contents[6].string
            achievement = row.contents[1].string.title()
            apiname = row.contents[1].string

            points.append({
                    "measurement": "achievement",
                    "time": date,
                    "tags": {
                        "platform": "Google Play",
                        "title": game,
                        "apiname": apiname
                    },
                    "fields": {
                        "name": achievement
                    }
                })

if not os.path.isdir('Takeout/Google Play Games Services/Games'):
    logging.error("Google Takeout files not found. Please extract the archive into Takeout/")
    sys.exit(1)

connect(GAMING_DATABASE)

for game in os.listdir('Takeout/Google Play Games Services/Games/'):
    if os.path.isfile(f'Takeout/Google Play Games Services/Games/{game}/Activity.html'):
        parse_activity(game)
    if os.path.isfile(f'Takeout/Google Play Games Services/Games/{game}/Experience.html'):
        parse_achievements(game)

write_points(points)
