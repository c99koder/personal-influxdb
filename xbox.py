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

import requests, sys, re
from datetime import datetime, date
from bs4 import BeautifulSoup
from config import *

if not TRUE_ACHIEVEMENTS_ID:
    logging.error("TRUE_ACHIEVEMENTS_ID not set in config.py")
    sys.exit(1)

points = []

connect(XBOX_DATABASE)

try:
    response = requests.get(f'https://www.trueachievements.com/gamer/{XBOX_GAMERTAG}/achievements?executeformfunction&function=AjaxList&params=oAchievementList%7C%26ddlPlatformIDs%3D%26ddlGenreIDs%3D%26ddlDLCFilter%3DInclude%20DLC%26ddlFlagIDs%3D%26ddlGamerScore%3D-1%26AchievementFilter%3DrdoAchievementsIHave%26chkExcludeDoneWith%3DTrue%26oAchievementList_Order%3DWonTimeStamp%26oAchievementList_Page%3D1%26oAchievementList_ItemsPerPage%3D100%26oAchievementList_ResponsiveMode%3DTrue%26oAchievementList_TimeZone%3DEastern%20Standard%20Time%26oAchievementList_ShowAll%3DFalse%26txtHideUnobtainableAchievement%3DFalse%26txtGamerID%3D{TRUE_ACHIEVEMENTS_ID}%26txtEasy%3DFalse%26txtShowDescriptions%3DTrue%26txtAlwaysShowUnlockedAchievementDescriptions%3DFalse%26txtYearWon%3D0%26txtMinRatio%3D0%26txtMaxRatio%3D0%26txtMaxTrueAchievement%3D0%26txtLastCharAlpha%3DFalse%26txtFirstCharAlpha%3DFalse%26txtOnlySecret%3DFalse%26txtChallenges%3DFalse%26txtContestID%3D0%26txtUseStringSQL%3DTrue%26txtOddGamerScore%3DFalse%26txtAchievementNameCharacters%3D0')
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    logging.error("HTTP request failed: %s", err)
    sys.exit(1)
html = BeautifulSoup(response.text, 'html.parser')

table = html.find('table', id='oAchievementList')
for row in table.find_all('tr'):
    if row['class'][0] == 'odd' or row['class'][0] == 'even':
        if row.find('td', class_='date').string != 'Offline':
            date = datetime.strptime(row.find('td', class_='date').string, '%d %b %y')
            game = row.find('td', class_='gamethumb').find('img')['alt']
            icon = 'https://www.trueachievements.com' + row.find('td', class_='achthumb').find('img')['src'].replace('/thumbs/', '/')
            achievement = row.find('td', class_='wideachievement').find('a').string
            description = list(row.find('td', class_='wideachievement').find('span').stripped_strings)[0]
            apiname = re.search('(?<=/)\w+', row.find('td', class_='achthumb').find('a')['href'])[0]

            points.append({
                    "measurement": "achievement",
                    "time": date.isoformat(),
                    "tags": {
                        "player_id": TRUE_ACHIEVEMENTS_ID,
                        "platform": "Xbox Live",
                        "player_name": XBOX_GAMERTAG,
                        "title": game,
                        "apiname": apiname
                    },
                    "fields": {
                        "name": achievement,
                        "description": description,
                        "icon": icon
                    }
                })

write_points(points)
