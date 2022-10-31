# Personal-InfluxDB

Import personal data from various APIs into InfluxDB

## Configuration

Open `config.py` and set your API credentials and InfluxDB server configuration at the top of the file

* __RescueTime__: Register for an API key at https://www.rescuetime.com/anapi/manage
* __Foursquare__: Register an app at https://foursquare.com/developers/ and generate an OAuth2 access token
* __Fitbit__: Register a "Personal" app at https://dev.fitbit.com/ and generate an OAuth2 access token
* __Steam__: Register for an API key at https://steamcommunity.com/dev/apikey and look up your SteamID at https://steamidfinder.com/ (use the `steamID64 (Dec)` value)
* __Nintendo Switch__: You'll need to set up [mitmproxy](https://mitmproxy.org/) and intercept the Nintendo Switch Parent Controls app on an iOS or Android device to grab your authentication tokens and device IDs
* __Xbox Live__: Register a profile at https://www.trueachievements.com/ and link it to your Xbox account. You can get your ID number by clicking your "TrueAchievement Points" score on your profile and looking at the leaderboard URL, it will be the `findgamerid` parameter.
* __Google Play Games__: Download your Google Play Games archive from https://takeout.google.com/ and extract it in the same folder as the script
* __Todoist__: *Access to the API requires a Todoist Premium subscription* Create an app at https://developer.todoist.com/appconsole.html and generate a test token
* __GitHub__: Create a personal access token at https://github.com/settings/tokens
* __Trakt.tv__: Register for an API key at https://trakt.tv/oauth/applications and generate an OAuth2 access token, you'll also need to create an API key at https://www.themoviedb.org/settings/api to download movie / show posters
* __EDSM__: Generate an API key at https://www.edsm.net/en/settings/api
* __Exist__: Register an app at https://exist.io/account/apps/
* __RetroPie__: Place the shell files and python script into user `pi`'s home directory. Created or edit `/opt/retropie/configs/all/runcommand-onstart.sh` and append the line `bash "/home/pi/influx-onstart.sh" "$@"`. Create or edit `/opt/retropie/configs/all/runcommand-onend.sh` and append the line `bash "/home/pi/influx-onend.sh" "$@"`
* __FsHub.io__: Generate a personal access token at https://fshub.io/settings/integrations and set your pilot ID to the number in your "Personal Dashboard" URL
* __Stadia__: Link your Stadia account to [Exophase](https://www.exophase.com/) and then set your Exophase username and Stadia nickname
* __PSN__: Link your PSN account to [Exophase](https://www.exophase.com/) and then set your Exophase username and PSN nickname
* __LibreLinkUp__: Open the Freestyle Libre app and choose `Connected Apps` from the menu, then send yourself an invite to `LibreLinkUp`. Install the `LibreLinkUp` app on your phone and accept the invitation, then set your username and password in the configuration file.

## Usage

Check your Python version and make sure version 3.7 or newer is installed on your system:

```shell
$ python3 --version
```

Install required python3 modules:

```shell
$ pip3 install pytz influxdb requests requests-cache instaloader todoist-python trakt.py publicsuffix2 logging colorlog bs4
```

Run each Python script from the terminal and it will insert the most recent data into InfluxDB.

## Notes

* Each script is designed to write to its own InfluxDB database.  Using the same database name between scripts can lead to data being unexpectedly overwritten or deleted.
* RescueTime provides data each hour, so scheduling the script as an hourly cron job is recommended.
* Steam provides the recent playtime over 2 weeks, so the first set of data inserted will contain 2 weeks of time.  New data going forward will be more accurate as the script will calculate the time since the last run.
* Google Play doesn't provide total play time, only achievements and last played timestamps
* Instagram can take a very long time to download, so by default it will only fetch the 10 most recent posts.  Set `MAX_POSTS` to `0` to download everything.
* Access to the Todoist API requires a premium subscription

## Grafana Dashboards

The [grafana](grafana/) folder contains json files for various example dashboards.
Most dashboards require the `grafana-piechart-panel` plugin, and the Foursquaure panel also requires the panodata `grafana-map-panel` plugin:

```shell
$ grafana-cli plugins install grafana-piechart-panel
$ grafana-cli --pluginUrl grafana-cli --pluginUrl https://github.com/panodata/grafana-map-panel/releases/download/0.15.0/grafana-map-panel-0.15.0.zip plugins install grafana-map-panel plugins install grafana-map-panel
```

### RescueTime dashboard

![Grafana RescueTime Screenshot](https://raw.githubusercontent.com/c99koder/personal-influxdb/master/screenshots/grafana-rescuetime.png)

### Fitbit dashboard

![Grafana Fitbit Screenshot](https://raw.githubusercontent.com/c99koder/personal-influxdb/master/screenshots/grafana-fitbit.png)

### Gaming dashboard

![Grafana Gaming Screenshot](https://raw.githubusercontent.com/c99koder/personal-influxdb/master/screenshots/grafana-gaming.png)

### Foursquare dashboard

![Grafana Foursquare Screenshot](https://raw.githubusercontent.com/c99koder/personal-influxdb/master/screenshots/grafana-foursquare.png)

### Instagram dashboard

![Grafana Instagram Screenshot](https://raw.githubusercontent.com/c99koder/personal-influxdb/master/screenshots/grafana-instagram.png)

### Todoist dashboard

![Grafana Todoist Screenshot](https://raw.githubusercontent.com/c99koder/personal-influxdb/master/screenshots/grafana-todoist.png)

### GitHub dashboard

![Grafana GitHub Screenshot](https://raw.githubusercontent.com/c99koder/personal-influxdb/master/screenshots/grafana-github.png)

### Trakt.tv dashboard

![Grafana Trakt.tv Screenshot](https://raw.githubusercontent.com/c99koder/personal-influxdb/master/screenshots/grafana-trakt.png)

### EDSM dashboard

![Grafana EDSM Screenshot](https://raw.githubusercontent.com/c99koder/personal-influxdb/master/screenshots/grafana-edsm.png)

### Exist dashboard

![Grafana Exist Screenshot](https://raw.githubusercontent.com/c99koder/personal-influxdb/master/screenshots/grafana-exist.png)

### FsHub.io dashboard

![Grafana FsHub.io Screenshot](https://raw.githubusercontent.com/c99koder/personal-influxdb/master/screenshots/grafana-fshub.png)

# License

Copyright (C) 2022 Sam Steele. Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
