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

import sys, logging, colorlog, pytz
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

LOCAL_TIMEZONE = pytz.timezone('America/New_York')

# InfluxDB Configuration
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_CHUNK_SIZE = 50 # How many points to send per request

# Shared gaming database
GAMING_DATABASE = 'gaming'

# EDSM configuration
EDSM_API_KEY = ''
EDSM_COMMANDER_NAME = ''
EDSM_DATABASE = 'edsm'

# Exist.io configuration
EXIST_ACCESS_TOKEN = ''
EXIST_USERNAME = ''
EXIST_DATABASE = 'exist'
EXIST_USE_FITBIT = True
EXIST_USE_TRAKT = True
EXIST_USE_GAMING = True
EXIST_USE_RESCUETIME = False

# Fitbit configuration
FITBIT_LANGUAGE = 'en_US'
FITBIT_CLIENT_ID = ''
FITBIT_CLIENT_SECRET = ''
FITBIT_ACCESS_TOKEN = ''
FITBIT_INITIAL_CODE = ''
FITBIT_REDIRECT_URI = 'https://www.example.net'
FITBIT_DATABASE = 'fitbit'

# Foursquare configuration
FOURSQUARE_ACCESS_TOKEN = ''
FOURSQUARE_DATABASE = 'foursquare'

# FSHub configuration
FSHUB_API_KEY = ''
FSHUB_PILOT_ID = ''
FSHUB_DATABASE = 'fshub'

# GitHub configuration
GITHUB_API_KEY = ''
GITHUB_USERNAME = ''
GITHUB_DATABASE = 'github'

# Instagram configuration
INSTAGRAM_PROFILE = ''
INSTAGRAM_DATABASE = 'instagram'
INSTAGRAM_MAX_POSTS = 10 #set to 0 to download all posts

# Freestyle LibreLinkUp configuration
LIBRELINKUP_USERNAME = ''
LIBRELINKUP_PASSWORD = ''
LIBRELINKUP_DATABASE = 'glucose'
LIBRELINKUP_URL = 'https://api-us.libreview.io'
LIBRELINKUP_VERSION = '4.7.0'
LIBRELINKUP_PRODUCT = 'llu.ios'

# Nintendo Switch configuration
NS_DEVICE_ID = ''
NS_SMART_DEVICE_ID = ''
NS_SESSION_TOKEN = ''
NS_CLIENT_ID = ''
# These occasionally need to be updated when Nintendo changes the minimum allowed version
NS_INTERNAL_VERSION = '321'
NS_DISPLAY_VERSION = '1.17.0'
NS_OS_VERSION = '15.2'
NS_DATABASE = GAMING_DATABASE

# OneTouch Reveal configuration
ONETOUCH_USERNAME = ''
ONETOUCH_PASSWORD = ''
ONETOUCH_URL = 'https://app.onetouchreveal.com'
ONETOUCH_DATABASE = 'glucose'

# RescueTime configuration
RESCUETIME_API_KEY = ''
RESCUETIME_DATABASE = 'rescuetime'

# RetroAchievements configuration
RA_API_KEY = ''
RA_USERNAME = ''
RA_DATABASE = GAMING_DATABASE

# RetroArch configuration
RETROARCH_LOGS = '/home/ark/.config/retroarch/playlists/logs/'
EMULATIONSTATION_ROMS = '/roms'
RETROARCH_IMAGE_WEB_PREFIX = 'https://example.net/retroarch_images/'

# Exophase configuration for Stadia and PSN
EXOPHASE_NAME = ''

# Stadia configuration
STADIA_NAME = ''
STADIA_DATABASE = GAMING_DATABASE

# PSN configuration
PSN_NAME = ''
PSN_DATABASE = GAMING_DATABASE

# Steam configuration
STEAM_API_KEY = ''
STEAM_ID = ''
STEAM_USERNAME = ''
STEAM_LANGUAGE = 'en'
STEAM_DATABASE = GAMING_DATABASE

# Todoist configuration
TODOIST_ACCESS_TOKEN = ''
TODOIST_DATABASE = 'todoist'

# Trakt.tv configuration
TRAKT_CLIENT_ID = ''
TRAKT_CLIENT_SECRET = ''
TRAKT_OAUTH_CODE = ''
TMDB_API_KEY = ''
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/'
TRAKT_DATABASE = 'trakt'

# Xbox configuration
XBOX_GAMERTAG = ''
TRUE_ACHIEVEMENTS_ID = ''
XBOX_DATABASE = GAMING_DATABASE

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s %(log_color)s%(message)s'
LOG_COLORS = {
    'WARNING':  'yellow',
    'ERROR':    'red',
    'CRITICAL': 'red',
	}

def connect(db):
    global client
    try:
        logging.info("Connecting to %s:%s", INFLUXDB_HOST, INFLUXDB_PORT)
        client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
        client.create_database(db)
        client.switch_database(db)
    except InfluxDBClientError as err:
        logging.error("InfluxDB connection failed: %s", err)
        sys.exit(1)
    return client

def write_points(points):
    total = len(points)
    global client
    try:
        start = 0
        end = INFLUXDB_CHUNK_SIZE
        while start < len(points):
            if end > len(points):
                end = len(points)

            client.write_points(points[start:end])
            logging.debug(f"Wrote {end} / {total} points")

            start = end
            end = end + INFLUXDB_CHUNK_SIZE
    except InfluxDBClientError as err:
        logging.error("Unable to write points to InfluxDB: %s", err)
        sys.exit(1)

    logging.info("Successfully wrote %s data points to InfluxDB", total)

client = None

if sys.stdout.isatty():
    colorlog.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, log_colors=LOG_COLORS, stream=sys.stdout)
else:
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT.replace(f'%(log_color)s', ''), stream=sys.stdout)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception