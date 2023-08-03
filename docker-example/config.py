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

import sys, logging, colorlog, pytz, os
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

TIMEZONE = os.getenv('TZ', 'America/Los_Angeles')
LOCAL_TIMEZONE = pytz.timezone(TIMEZONE)

# InfluxDB Configuration
INFLUXDB_HOST = os.getenv('INFLUXDB_HOST')
INFLUXDB_PORT = os.getenv('INFLUXDB_PORT', 8086)
INFLUXDB_USERNAME = os.getenv('INFLUXDB_USER', 'admin')
INFLUXDB_PASSWORD = os.getenv('INFLUXDB_PASSWORD', 'admin')
INFLUXDB_CHUNK_SIZE = 50 # How many points to send per request

# Freestyle LibreLinkUp configuration
LIBRELINKUP_USERNAME = os.getenv('LIBRELINKUP_USERNAME')
LIBRELINKUP_PASSWORD = os.getenv('LIBRELINKUP_PASSWORD')
LIBRELINKUP_DATABASE = os.getenv('LIBRELINKUP_DATABASE')
LIBRELINKUP_URL = 'https://api-us.libreview.io'
LIBRELINKUP_VERSION = '4.7.0'
LIBRELINKUP_PRODUCT = 'llu.ios'

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