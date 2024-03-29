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
from datetime import datetime, date, timedelta
from config import *

if not FOURSQUARE_ACCESS_TOKEN:
    logging.error("FOURSQUARE_ACCESS_TOKEN not set in config.py")
    sys.exit(1)

points = []

us_states = {
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'District of Columbia': 'DC',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Northern Mariana Islands':'MP',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Palau': 'PW',
    'Pennsylvania': 'PA',
    'Puerto Rico': 'PR',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virgin Islands': 'VI',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY',
}

def fetch_checkins(offset):
    try:
        response = requests.get('https://api.foursquare.com/v2/users/self/checkins',
            params={'sort': 'newestfirst', 'offset': offset, 'oauth_token':FOURSQUARE_ACCESS_TOKEN, 'v':'20191201', 'limit':250})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error("HTTP request failed: %s", err)
        sys.exit(1)

    data = response.json()
    logging.info("Got %s checkins from Foursquare", len(data['response']['checkins']['items']))

    for item in data['response']['checkins']['items']:
        cat = ''
        if 'venue' in item:
            for category in item['venue']['categories']:
                if category['primary']:
                    cat = category['name']
            tags = {
                "category": cat,
                "venue_id": item['venue']['id'],
                "venue_name": item['venue']['name'],
                "mayor": item['isMayor']
            }
            if 'country' in item['venue']['location']:
                tags['country'] = item['venue']['location']['country']
            if 'city' in item['venue']['location']:
                tags['city'] = item['venue']['location']['city']
            if 'state' in item['venue']['location']:
                if item['venue']['location']['state'] in us_states:
                    tags['state'] = us_states[item['venue']['location']['state']]
                else:
                    tags['state'] = item['venue']['location']['state']
            points.append({
                    "measurement": "checkin",
                    "time": datetime.fromtimestamp(item['createdAt']).isoformat(),
                    "tags": tags,
                    "fields": {
                        "latitude": float(item['venue']['location']['lat']),
                        "longitude": float(item['venue']['location']['lng'])
                    }
                })

    return len(data['response']['checkins']['items'])

connect(FOURSQUARE_DATABASE)
fetch_checkins(0)
write_points(points)
