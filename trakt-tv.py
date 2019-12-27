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

import requests, sys, os, json
from datetime import datetime, date
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from trakt import Trakt
from trakt.objects import Episode, Show, Movie

TRAKT_CLIENT_ID = ''
TRAKT_CLIENT_SECRET = ''
TRAKT_OAUTH_CODE = ''
TMDB_API_KEY = ''
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/'
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'trakt'
points = []
posters = {}

def fetch_poster(type, tmdb_id):
	print("Fetching poster for type=" + type + " id=" + tmdb_id)
	try:
		response = requests.get('https://api.themoviedb.org/3/' + type + '/' + tmdb_id, 
			params={'api_key': TMDB_API_KEY})
		response.raise_for_status()
	except requests.exceptions.HTTPError as err:
		print("HTTP request failed: %s" % (err))
		return None

	data = response.json()
	if 'poster_path' in data and data['poster_path'] != None:
		return TMDB_IMAGE_BASE + 'w154' + data['poster_path']
	else:
		return None

try:
	client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
	client.create_database(INFLUXDB_DATABASE)
	client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
	print("InfluxDB connection failed: %s" % (err))
	sys.exit()

Trakt.configuration.defaults.client(
	id=TRAKT_CLIENT_ID,
	secret=TRAKT_CLIENT_SECRET
)

if not os.path.exists(".trakt.json"):
	auth = Trakt['oauth'].token_exchange(TRAKT_OAUTH_CODE, 'urn:ietf:wg:oauth:2.0:oob')
	with open('.trakt.json', 'w') as outfile:
		json.dump(auth, outfile)
else:
	with open('.trakt.json') as json_file:
		auth = json.load(json_file)

Trakt.configuration.defaults.oauth.from_response(auth)

for item in Trakt['sync/history'].get(pagination=True, per_page=100, start_at=datetime(date.today().year, date.today().month, 1)):
	if item.action == "watch":
		if isinstance(item, Episode):
			if not item.show.get_key('tmdb') in posters:
				posters[item.show.get_key('tmdb')] = fetch_poster('tv', item.show.get_key('tmdb'))
			if posters[item.show.get_key('tmdb')] == None:
				html = None
			else:
				html = '<img src="' + posters[item.show.get_key('tmdb')] + '"/>'
			points.append({
					"measurement": "watch",
					"time": item.watched_at.isoformat(),
					"tags": {
						"id": item.get_key('trakt'),
						"show": item.show.title,
						"show_id": item.show.get_key('trakt'),
						"season": item.pk[0],
						"episode": item.pk[1],
						"type": "episode"
					},
					"fields": {
						"title": item.title,
						"tmdb_id": item.show.get_key('tmdb'),
						"poster": posters[item.show.get_key('tmdb')],
						"poster_html": html,
						"slug": item.show.get_key('slug'),
						"url": "https://trakt.tv/shows/" + item.show.get_key('slug'),
						"episode_url": "https://trakt.tv/shows/" + item.show.get_key('slug') + "/seasons/" + str(item.pk[0]) + "/episodes/" + str(item.pk[1])
					}
			})
		if isinstance(item, Movie):
			if not item.get_key('tmdb') in posters:
				posters[item.get_key('tmdb')] = fetch_poster('movie', item.get_key('tmdb'))
			if posters[item.get_key('tmdb')] == None:
				html = None
			else:
				html = '<img src="' + posters[item.get_key('tmdb')] + '"/>'
			points.append({
					"measurement": "watch",
					"time": item.watched_at.isoformat(),
					"tags": {
						"id": item.get_key('trakt'),
						"type": "movie"
					},
					"fields": {
						"title": item.title,
						"tmdb_id": item.get_key('tmdb'),
						"poster": posters[item.get_key('tmdb')],
						"poster_html": html,
						"slug": item.get_key('slug'),
						"url": "https://trakt.tv/movie/" + item.get_key('slug')
					}
				})

try:
	client.write_points(points)
except InfluxDBClientError as err:
	print("Unable to write points to InfluxDB: %s" % (err))
	sys.exit()

print("Successfully wrote %s data points to InfluxDB" % (len(points)))
