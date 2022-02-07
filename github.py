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
from config import *

if not GITHUB_API_KEY:
    logging.error("GITHUB_API_KEY not set in config.py")
    sys.exit(1)

def add_week(week):
    if week['c'] > 0:
        points.append({
            "measurement": "commits",
            "time": datetime.fromtimestamp(week['w']).isoformat(),
            "tags": {
                "username": GITHUB_USERNAME,
                "repo": repo['full_name']
            },
            "fields": {
                "value": week['c']
            }
        })

connect(GITHUB_DATABASE)

try:
    response = requests.get('https://api.github.com/user/repos',
        params={'sort': 'pushed', 'per_page':10},
        headers={'Authorization': f'token {GITHUB_API_KEY}', 'User-Agent': GITHUB_USERNAME})
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    logging.error("HTTP request failed: %s", err)
    sys.exit(1)

repos = response.json()
if len(repos) == 0:
    logging.error("No GitHub repos found")
    sys.exit(1)
logging.info("Got %s repos from GitHub", len(repos))

points = []

for repo in repos:
    logging.info("Fetch statistics for %s", repo['full_name'])
    try:
        response = requests.get(repo['url'] + '/stats/contributors',
            params={'sort': 'pushed'},
            headers={'Authorization': f'token {GITHUB_API_KEY}', 'User-Agent': GITHUB_USERNAME})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("HTTP request failed: %s" % (err))
        sys.exit()

    contributors = response.json()
    for contributor in contributors:
        if contributor['author']['login'] == GITHUB_USERNAME:
#            adding all the old data each time causes a lot of stress on InfluxDB
#            for week in contributor['weeks']:
#                add_week(week)
            if len(contributor['weeks']) > 0:
                add_week(contributor['weeks'][len(contributor['weeks']) - 1])
            if len(contributor['weeks']) > 1:
                add_week(contributor['weeks'][len(contributor['weeks']) - 2])

write_points(points)
