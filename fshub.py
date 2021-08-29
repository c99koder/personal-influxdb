#!/usr/bin/python3

#  Copyright (C) 2020 Sam Steele
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

import requests, requests_cache, sys, math
from datetime import datetime, date, timedelta
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

FSHUB_API_KEY = ''
FSHUB_PILOT_ID = ''
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USERNAME = 'root'
INFLUXDB_PASSWORD = 'root'
INFLUXDB_DATABASE = 'fshub'
points = []

def fetch(limit, cursor):
    try:
        response = requests.get('https://fshub.io/api/v3/pilot/' + FSHUB_PILOT_ID + '/flight',
            params={'limit': limit, 'cursor': cursor},
            headers={'X-Pilot-Token': FSHUB_API_KEY, 'Content-Type': 'application/json'})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("HTTP request failed: %s" % (err))
        sys.exit()

    data = response.json()
    print("Got flights %s from FsHub" % (len(data['data'])))

    for flight in data['data']:
        if flight['departure'] != None and flight['departure']['icao'] != None and flight['arrival'] != None and flight['arrival']['icao'] != None:
            points.append({
                "measurement": "flight",
                "time": flight['departure']['time'],
                "tags": {
                    "flight_id": flight['id'],
                    "pilot_id": flight['user']['id']
                },
                "fields": {
                    "aircraft": flight['aircraft']['name'],
                    "fuel_used": flight['fuel_used'],
                    "landing_rate": flight['landing_rate'],
                    "distance_nm": flight['distance']['nm'],
                    "distance_km": flight['distance']['km'],
                    "max_alt": flight['max']['alt'],
                    "max_spd": flight['max']['spd'],
                    "duration": flight['time'],
                    "departure_icao": flight['departure']['icao'],
                    "departure_iata": flight['departure']['iata'],
                    "departure_name": flight['departure']['name'],
                    "departure_time": flight['departure']['time'],
                    "departure_lat": flight['departure']['geo']['lat'],
                    "departure_long": flight['departure']['geo']['lng'],
                    "departure_hdg_mag": flight['departure']['hdg']['mag'],
                    "departure_hdg_true": flight['departure']['hdg']['true'],
                    "departure_spd": flight['departure']['spd']['tas'],
                    "depature_fuel": flight['departure']['fuel'],
                    "depature_pitch": flight['departure']['pitch'],
                    "depature_bank": flight['departure']['bank'],
                    "depature_wind_spd": flight['departure']['wind']['spd'],
                    "depature_wind_dir": flight['departure']['wind']['dir'],
                    "departure_url": "https://fshub.io/airport/" + flight['departure']['icao'].upper(),
                    "arrival_icao": flight['arrival']['icao'],
                    "arrival_iata": flight['arrival']['iata'],
                    "arrival_name": flight['arrival']['name'],
                    "arrival_time": flight['arrival']['time'],
                    "arrival_lat": flight['arrival']['geo']['lat'],
                    "arrival_long": flight['arrival']['geo']['lng'],
                    "arrival_hdg_mag": flight['arrival']['hdg']['mag'],
                    "arrival_hdg_true": flight['arrival']['hdg']['true'],
                    "arrival_spd": flight['arrival']['spd']['tas'],
                    "arrival_fuel": flight['arrival']['fuel'],
                    "arrival_pitch": flight['arrival']['pitch'],
                    "arrival_bank": flight['arrival']['bank'],
                    "arrival_wind_spd": flight['arrival']['wind']['spd'],
                    "arrival_wind_dir": flight['arrival']['wind']['dir'],
                    "arrival_url": "https://fshub.io/airport/" + flight['arrival']['icao'].upper(),
                    "flight_url": "https://fshub.io/flight/" + str(flight['id']),
                    "pilot_url": "https://fshub.io/pilot/" + str(flight['user']['id'])
                }
            })
            points.append({
                "measurement": "airport",
                "time": flight['departure']['time'],
                "tags": {
                    "flight_id": flight['id'],
                    "pilot_id": flight['user']['id'],
                    "icao": flight['departure']['icao'],
                    "iata": flight['departure']['iata']
                },
                "fields": {
                    "name": flight['departure']['name'],
                    "lat": flight['departure']['geo']['lat'],
                    "long": flight['departure']['geo']['lng'],
                    "url": "https://fshub.io/airport/" + flight['departure']['icao'].upper()
                }
            })
            points.append({
                "measurement": "airport",
                "time": flight['arrival']['time'],
                "tags": {
                    "flight_id": flight['id'],
                    "pilot_id": flight['user']['id'],
                    "icao": flight['arrival']['icao'],
                    "iata": flight['arrival']['iata']
                },
                "fields": {
                    "name": flight['arrival']['name'],
                    "lat": flight['arrival']['geo']['lat'],
                    "long": flight['arrival']['geo']['lng'],
                    "url": "https://fshub.io/airport/" + flight['arrival']['icao'].upper()
                }
            })
    if data['meta']['cursor']['count'] == limit:
        return data['meta']['cursor']['next']
    else:
        return -1

try:
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USERNAME, password=INFLUXDB_PASSWORD)
    client.create_database(INFLUXDB_DATABASE)
    client.switch_database(INFLUXDB_DATABASE)
except InfluxDBClientError as err:
    print("InfluxDB connection failed: %s" % (err))
    sys.exit()

cursor = 0

while cursor != -1:
    cursor = fetch(100,cursor)

    try:
        client.write_points(points)
    except InfluxDBClientError as err:
        print("Unable to write points to InfluxDB: %s" % (err))
        sys.exit()

    print("Successfully wrote %s data points to InfluxDB" % (len(points)))
    points = []
