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
from datetime import datetime, date, timedelta, time
from config import *

if not RA_API_KEY:
    logging.error("RA_API_KEY not set in config.py")
    sys.exit(1)

points = []
connect(RA_DATABASE)

end = datetime.utcnow().timestamp()
start = end - 604800

try:
    response = requests.get('https://retroachievements.org/API/API_GetAchievementsEarnedBetween.php',
        params={'z': RA_USERNAME, 'y': RA_API_KEY, 'u': RA_USERNAME, 'f': start, 't': end})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    logging.error("HTTP request failed: %s", err)
    sys.exit(1)

data = response.json()
logging.info("Got %s achievements from RetroAchievements", len(data))

for achievement in data:
    date = datetime.strptime(achievement['Date'], "%Y-%m-%d %H:%M:%S")

    points.append({
            "measurement": "achievement",
            "time": date.isoformat(),
            "tags": {
                "player_id": RA_USERNAME,
                "platform": achievement['ConsoleName'],
                "player_name": RA_USERNAME,
                "title": achievement['GameTitle'],
                "application_id": str(achievement['GameID']),
                "apiname": str(achievement['AchievementID']),
            },
            "fields": {
                "name": achievement['Title'],
                "description": achievement['Description'],
                "icon": f'https://retroachievements.org{achievement["BadgeURL"]}'
            }
    })

write_points(points)
