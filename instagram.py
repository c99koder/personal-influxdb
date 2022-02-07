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

import sys
from datetime import datetime
from instaloader import instaloader, Profile
from config import *

if not INSTAGRAM_PROFILE:
    logging.error("INSTAGRAM_PROFILE not set in config.py")
    sys.exit(1)

points = []

connect(INSTAGRAM_DATABASE)

logging.info("Fetching profile for %s", INSTAGRAM_PROFILE)
L = instaloader.Instaloader()
try:
    L.load_session_from_file(INSTAGRAM_PROFILE)
except FileNotFoundError:
    logging.warn("Logging into Instagram can make this script more reliable. Try: instaloader -l {INSTAGRAM_PROFILE}")

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
logging.info("Got %s posts from Instagram", count)
if INSTAGRAM_MAX_POSTS == 0:
    INSTAGRAM_MAX_POSTS = count

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
            "url": f'https://instagram.com/p/{post.shortcode}/',
            "thumbnail_html": f'<img width="100%" height="100%" src="{post.url}"/>',
            "caption": post.caption,
            "likes": post.likes,
            "comments": post.comments
        }
    })

    logging.debug("%s / %s", len(points), INSTAGRAM_MAX_POSTS)

    if len(points) > INSTAGRAM_MAX_POSTS:
        break
    
write_points(points)