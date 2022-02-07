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

import requests, pytz, sys
from datetime import datetime
from config import *

if not RESCUETIME_API_KEY:
    logging.error("RESCUETIME_API_KEY not set in config.py")
    sys.exit(1)

connect(RESCUETIME_DATABASE)

try:
    response = requests.get('https://www.rescuetime.com/anapi/data',
        params={"key":RESCUETIME_API_KEY, "perspective":"interval", "restrict_kind":"activity", "format":"json"})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    logging.error("HTTP request failed: %s", err)
    sys.exit(1)

activities = response.json()
logging.info("Got %s activites from RescueTime", len(activities['rows']))
if len(activities['rows']) == 0:
    sys.exit()

points = []

for activity in activities['rows']:
    time = datetime.fromisoformat(activity[0])
    utc_time = LOCAL_TIMEZONE.localize(time).astimezone(pytz.utc).isoformat()
    points.append({
            "measurement": "activity",
            "time": utc_time,
            "tags": {
                "activity": activity[3],
                "category": activity[4]
            },
            "fields": {
                "duration": activity[1],
                "productivity": activity[5],
            }
        })

write_points(points)
