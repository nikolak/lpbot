# -*- coding: utf-8 -*-

# Copyright 2014 Nikola Kovacevic <nikolak@outlook.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import OrderedDict
import requests
import urllib.request, urllib.parse, urllib.error
import re

from lpbot.module import commands, example, rule
from lpbot import tools

http_url_regex = "https?://open.spotify.com/(\w+)/(\S+)"
spotify_uri_regex = "spotify:(\w+):(\S+)"
http_regex = re.compile(http_url_regex)
uri_regex = re.compile(spotify_uri_regex)


def setup(bot):
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.lpbotMemory()
    bot.memory['url_callbacks'][http_regex] = catch_spotify_url
    bot.memory['url_callbacks'][uri_regex] = catch_spotify_url


def shutdown(bot):
    del bot.memory['url_callbacks'][http_regex]
    del bot.memory['url_callbacks'][uri_regex]

def _milliseconds_to_hms(milliseconds):
    """Takes a number of milliseconds and turns it into hours, minutes and seconds

    Args:
        milliseconds: (int) number of milliseconds to convert

    Returns:
        A tuple (hours, minutes, seconds)
    """

    seconds, _ = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return (hours, minutes, seconds)

def _search_spotify(query):
    """
    Docs: https://developer.spotify.com/web-api/search-item/
    Endpoint: GET https://api.spotify.com/v1/search
    Category: `album`, `artist` or `track`
    """
    category = None
    if not query:
        return

    if query.split(":")[0] == query:
        category = "track"
    else:
        category = query.split(":")[0]

        if category not in ["album", "artist", "track"]:
            category = "track"
        else:
            query = query.replace(category + ":", "")

    params = OrderedDict([
        ('q', query),
        ('type', category),
        ('limit', "1")
    ])

    api_url = "https://api.spotify.com/v1/search?{}".format(
        urllib.parse.urlencode(params))

    r = requests.get(api_url)

    if r.status_code != 200:
        return "Error accessing Spotify API"

    spotify = r.json()[list(r.json().keys())[0]]

    try:
        if spotify['total'] == 0:
            return "Nothing found for {}".format(query)
    except KeyError:
        return "Spotify returned invalid json :("

    spotify = spotify['items'][0]
    if category == "track":
        return_msg = "[track] {artist} - {track} [{album}] ({duration}) - {url}"
        duration = _milliseconds_to_hms(spotify['duration_ms'])
        values = {
            'artist': spotify['artists'][0]['name'],
            'track': spotify['name'],
            'album': spotify['album']['name'],
            'duration': '{:02d}:{:02d}:{:02d}'.format(*duration),
            'url': spotify['external_urls']['spotify']
        }

        return return_msg.format(**values)
    elif category == "album":
        return_msg = "[album] {name} - {url}"
        name = spotify['name']
        url = spotify['external_urls']['spotify']
        return return_msg.format(name=name,
                                 url=url)
    elif category == "artist":
        # TODO: Add genres and stuff
        return_msg = "[artist] {name} - {url}"
        values = {
            'name': spotify['name'],
            'url': spotify['external_urls']['spotify']}

        return return_msg.format(**values)


def get_spotify_info(category, spotify_id):
    if category == "album":
        api_url = "https://api.spotify.com/v1/albums/{id}".format(id=spotify_id)
    elif category == "track":
        api_url = "https://api.spotify.com/v1/tracks/{id}".format(id=spotify_id)
    elif category == "artist":
        api_url = "https://api.spotify.com/v1/artists/{id}".format(id=spotify_id)
    else:
        return

    r = requests.get(api_url)
    if r.status_code != 200:
        return None

    spotify = r.json()

    if category == 'album':
        return_msg = "[album] {name} by {artist} ({year}) - {num_tracks} tracks"
        values = {
            'name': spotify['name'],
            'artist': spotify['artists'][0]['name'],
            'year': spotify['release_date'],
            'num_tracks': spotify['tracks']['total']
        }
        return return_msg.format(**values)

    elif category == 'track':
        return_msg = "[track] {artist} - {track} [{album}] ({duration})"
        duration = _milliseconds_to_hms(spotify['duration_ms'])
        values = {
            'artist': spotify['artists'][0]['name'],
            'track': spotify['name'],
            'album': spotify['album']['name'],
            'duration': '{:02d}:{:02d}:{:02d}'.format(*duration),
            'url': spotify['external_urls']['spotify']
        }
        return return_msg.format(**values)

    elif category == 'artist':
        return_msg = "[artist] {name}"
        values = {
            'name': spotify['name']
        }
        return return_msg.format(**values)

    else:
        return None


@rule('.*%s.*' % http_url_regex)
@rule('.*%s.*' % spotify_uri_regex)
def catch_spotify_url(bot, trigger, match=None):
    match = match or trigger
    category = match.group(1)
    spotify_id = match.group(2)

    if not category or not spotify_id:
        return

    if category not in ["album", "artist", "track"]:
        return

    try:
        msg = get_spotify_info(category.lower(), spotify_id)
    except:
        return

    if msg:
        bot.say("[Spotify] " + msg)


@commands('spotify')
@example('.spotify voodoo people')
@example('.spotify artist:the prodigy')
def search_spotify(bot, trigger):
    query = trigger.group(2)
    if query:
        msg = _search_spotify(query)

        if msg:
            bot.say("[Spotify] " + msg)
