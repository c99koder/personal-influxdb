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

import requests, sys
from datetime import datetime, date, timedelta
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from instaloader import instaloader, Profile

INSTAGRAM_PROFILE = ''
MAX_POSTS = 10 #set to 0 to download all posts
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'instagram'
points = []

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(INFLUXDB_DATABASE)
    client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

print("Fetching profile for " + INSTAGRAM_PROFILE)
L = instaloader.Instaloader()
profile = Profile.from_username(L.context, INSTAGRAM_PROFILE)
followers = profile.followers
points.append({
    "measurement": "followers",
    "time": datetime.utcnow().isoformat(),
    "tags": {
        "username": INSTAGRAM_PROFILE
    },
    "fields": {
        "value": followers
    }
})

posts = list(profile.get_posts())
count = len(posts)
print("Got %s posts from Instagram" % (count))
if MAX_POSTS == 0:
    MAX_POSTS = count

for post in posts:
    points.append({
        "measurement": "post",
        "time": post.date_utc.isoformat(),
        "tags": {
            "owner": post.owner_username,
            "shortcode": post.shortcode,
        },
        "fields": {
            "image": post.url,
            "url": 'https://instagram.com/p/' + post.shortcode + '/',
            "thumbnail_html": '<img width="100%" height="100%" src="' + post.url + '"/>',
            "caption": post.caption,
            "likes": post.likes,
            "comments": post.comments
        }
    })

    print("%s / %s" % (len(points), MAX_POSTS))

    if len(points) > MAX_POSTS:
        break;
    
try:
    client.write_points(points)
except InfluxDBClientError as err:
    print("Unable to write points to InfluxDB: %s" % (err))
    sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))
