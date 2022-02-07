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

import pytz
from datetime import datetime, date, timedelta, time
from config import *

games = {
  "angry-birds-vr-isle-of-pigs": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/1001140/header.jpg',
    "title": "Angry Birds VR: Isle of Pigs",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/1001140/'
  },
  "arcade": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/435490/header.jpg',
    "title": "Pierhead Arcade",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/435490/'
  },
  "cloudlands": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/425720/header.jpg',
    "title": "Cloudlands: VR Minigolf",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/425720/'
  },
  "fuji": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/589040/header.jpg',
    "title": "Fuji",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/589040/'
  },
  "half + half": {
    "image": 'https://halfandhalf.fun/assets/images/logo.png',
    "title": "Half + Half",
    "platform": "Oculus",
    "url": 'https://www.oculus.com/experiences/quest/2035353573194060/'
  },
  "openttd": {
    "image": 'https://www.openttd.org/static/img/layout/openttd-128.gif',
    "title": "OpenTTD",
    "platform": "Mac",
    "url": 'https://www.openttd.org'
  },
  "pixelripped1989": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/577530/header.jpg',
    "title": "Pixel Ripped 1989",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/577530/'
  },
  "proze-win64-shipping": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/924250/header.jpg',
    "title": "Proze: Enlightenment",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/924250/'
  },
  "shenmue3-win64-shipping": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/878670/header.jpg',
    "title": "Shenmue III",
    "platform": "Epic Games Store",
    "url": 'https://store.steampowered.com/app/878670/'
  },
  "starcitizen": {
    "image": 'https://robertsspaceindustries.com/rsi/static/wsc/images/Logo-SC@2x.png',
    "title": "Star Citizen",
    "platform": "Windows",
    "url": 'https://robertsspaceindustries.com/star-citizen'
  },
  "synthriders": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/885000/header.jpg',
    "title": "Synth Riders",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/885000/'
  },
  "the sims 4": {
    "image": 'https://media.contentapi.ea.com/content/dam/eacom/SIMS/brand-refresh-assets/images/2019/06/ts4-adaptive-logo-primary-white-7x2-xl-5x2-lg-2x1-md-16x9-sm-xs.png',
    "title": "The Sims 4",
    "platform": "Origin",
    "url": 'https://www.ea.com/games/the-sims/the-sims-4'
  },
  "transpose": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/835950/header.jpg',
    "title": "Transpose",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/835950/'
  },
  "twilightpath_Viveport": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/770110/header.jpg',
    "title": "Twilight Path",
    "platform": "Viveport",
    "url": 'https://store.steampowered.com/app/770110/'
  },
  "Solitaire": {
    "image": 'https://lh3.googleusercontent.com/trsFOWkeuVbmN40ss88nfXDxXcOiH1IF3oJJOueRvcrQEf0gMYsTCzGbC6C-kgqZow=s180-rw',
    "title": "Solitaire",
    "platform": "Android",
    "url": 'https://play.google.com/store/apps/details?id=com.mobilityware.solitaire'
  },
  "flightsimulator": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/1250410/header.jpg',
    "title": "Microsoft Flight Simulator",
    "platform": "Windows",
    "url": 'https://store.steampowered.com/app/1250410/'
  },
  "movingout": {
    "image": 'https://steamcdn-a.akamaihd.net/steam/apps/996770/header.jpg',
    "title": "Moving Out",
    "platform": "Windows",
    "url": 'https://store.steampowered.com/app/996770/'
  },
  "cengine": {
    "image": 'https://store-images.s-microsoft.com/image/apps.53972.13524928534337711.061b795b-d8df-4621-98ec-a96089e571a1.51af2134-99b3-46b4-bdd9-7c7f29c0655e?mode=scale&q=90&h=300&w=200',
    "title": "The Touryst",
    "platform": "Windows",
    "url": 'https://www.microsoft.com/en-us/p/the-touryst/9n9w1jk1x5qj'
  },
}
points = []
start_time = str(int(LOCAL_TIMEZONE.localize(datetime.combine(date.today(), time(0,0)) - timedelta(days=7)).astimezone(pytz.utc).timestamp()) * 1000) + 'ms'

client = connect(GAMING_DATABASE)
client.switch_database(RESCUETIME_DATABASE)
durations = client.query('SELECT "duration","activity" FROM "activity" WHERE time >= ' + start_time)
for duration in list(durations.get_points()):
    if duration['activity'] in games:
        points.append({
            "measurement": "time",
            "time": duration['time'],
            "tags": {
                "application_id": duration['activity'],
                "platform": games[duration['activity']]['platform'],
                "title": games[duration['activity']]['title'],
            },
            "fields": {
                "value": duration['duration'],
                "image": games[duration['activity']]['image'],
                "url": games[duration['activity']]['url']
            }
        })

client.switch_database(GAMING_DATABASE)
write_points(points)
