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

import requests, requests_cache, sys, os, json
from datetime import datetime, date
from trakt import Trakt
from trakt.objects import Episode, Movie
from config import *

if not TRAKT_CLIENT_ID:
    logging.error("TRAKT_CLIENT_ID not set in config.py")
    sys.exit(1)

points = []
posters = {}

def on_token_refreshed(response):
	global oauth_config_file
	with open(oauth_config_file, 'w') as outfile:
		json.dump(response, outfile)


def fetch_poster(type, tmdb_id):
	if tmdb_id == None:
		return None
	logging.debug("Fetching poster for type=%s id=%s", type, tmdb_id)
	try:
		with requests_cache.enabled('tmdb'):
			response = requests.get(f'https://api.themoviedb.org/3/{type}/{tmdb_id}', 
			params={'api_key': TMDB_API_KEY})
		response.raise_for_status()
	except requests.exceptions.HTTPError as err:
		logging.error("HTTP request failed: %s", err)
		return None

	data = response.json()
	if 'poster_path' in data and data['poster_path'] != None:
		return TMDB_IMAGE_BASE + 'w154' + data['poster_path']
	else:
		return None

connect(TRAKT_DATABASE)

Trakt.configuration.defaults.client(
	id=TRAKT_CLIENT_ID,
	secret=TRAKT_CLIENT_SECRET
)

script_dir = os.path.dirname(__file__)
oauth_config_file = os.path.join(script_dir, '.trakt.json')
if not os.path.exists(oauth_config_file):
	auth = Trakt['oauth'].token_exchange(TRAKT_OAUTH_CODE, 'urn:ietf:wg:oauth:2.0:oob')
	with open(oauth_config_file, 'w') as outfile:
		json.dump(auth, outfile)
else:
	with open(oauth_config_file) as json_file:
		auth = json.load(json_file)

Trakt.on('oauth.token_refreshed', on_token_refreshed)
Trakt.configuration.defaults.oauth.from_response(auth, refresh=True)

for item in Trakt['sync/history'].get(pagination=True, per_page=100, start_at=datetime(date.today().year, date.today().month, 1), extended='full'):
	if item.action == "watch" or item.action == "scrobble":
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
					"duration": item.show.runtime,
					"poster": posters[item.show.get_key('tmdb')],
					"poster_html": html,
					"slug": item.show.get_key('slug'),
					"url": f"https://trakt.tv/shows/{item.show.get_key('slug')}",
					"episode_url": f"https://trakt.tv/shows/{item.show.get_key('slug')}/seasons/{item.pk[0]}/episodes/{item.pk[1]}"
				}
			})
		if isinstance(item, Movie):
			if not item.get_key('tmdb') in posters:
				posters[item.get_key('tmdb')] = fetch_poster('movie', item.get_key('tmdb'))
			if posters[item.get_key('tmdb')] == None:
				html = None
			else:
				html = f'<img src="{posters[item.get_key("tmdb")]}"/>'
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
					"duration": item.runtime,
					"poster": posters[item.get_key('tmdb')],
					"poster_html": html,
					"slug": item.get_key('slug'),
					"url": f"https://trakt.tv/movie/{item.get_key('slug')}"
				}
			})

		if len(points) >= 5000:
			write_points(points)
			points = []

write_points(points)
