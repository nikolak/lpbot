# -*- coding: utf-8 -*-

# Copyright 2015 Nikola Kovacevic <nikolak@outlook.com>
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

import re

import requests
import arrow

from lpbot import tools
from lpbot.module import rule, commands, example


duration_regex = re.compile('PT(\d+H)?(\d+M)?(\d+S)?')
BASE_URL = "https://www.googleapis.com/youtube/v3"


def checkConfig(bot):
    if not bot.config.has_option('youtube', 'api_key'):
        return None
    else:
        return bot.config.youtube.api_key


def configure(config):
    """
    | [youtube]| example | purpose |
    | -------- | ------- | ------- |
    | api_key | ASkdasfn3k259283askdhSAT5OADOAKjbh | Youtube v3 API key |
    """
    chunk = ''
    if config.option('Configuring youtube module', False):
        config.interactive_add('youtube', 'api_key', 'Youtube v3 API key', '')
    return chunk


def setup(bot):
    bot.memory['yt_key'] = checkConfig(bot)


def get_video_info(api_key, video_id):
    video_url = "/videos" \
                "?part=contentDetails%2Cid%2CliveStreamingDetails%2Csnippet%2Cstatistics" \
                "&id={VIDEO_ID}" \
                "&key={API_KEY}".format(VIDEO_ID=video_id,
                                        API_KEY=api_key)

    endpoint = BASE_URL + video_url

    r = requests.get(endpoint)
    if r.status_code != 200:
        return None

    values = {}
    try:
        data = r.json()['items'][0]
    except:
        return None

    values['id'] = data['id']

    try:
        is_live = data['contentDetails']['duration'] == "PT0S" and data.get('liveStreamingDetails')
    except KeyError:
        is_live = False

    values['livestream'] = is_live

    values['title'] = data['snippet']['title']
    try:
        values['description'] = data['snipppet']['description']
    except KeyError:
        values['description'] = "N/A"

    try:
        values['uploader'] = data['snippet']['channelTitle']
    except KeyError:
        values['uploader'] = "N/A"

    if is_live:
        values['duration'] = "LIVE"
    else:
        try:
            duration = data['contentDetails']['duration']
            d = re.match(duration_regex, duration)
            d_values = [i for i in d.groups() if i is not None]
            values['duration'] = " ".join(d_values). \
                replace("H", "hr"). \
                replace("M", "min"). \
                replace("S", "sec")
        except:
            values['duration'] = "N/A"

    values['uploaded'] = arrow.get(data['snippet']['publishedAt']).humanize()
    try:
        views = data['statistics']['viewCount']
        values['views'] = str('{0:20,d}'.format(int(views))).lstrip(' ')
    except KeyError:
        values['views'] = "N/A"

    try:
        likes = data['statistics']['likeCount']
        values['likes'] = str('{0:20,d}'.format(int(likes))).lstrip(' ')
    except KeyError:
        values['likes'] = "N/A"

    try:
        dislikes = data['statistics']['dislikeCount']
        values['dislikes'] = str('{0:20,d}'.format(int(dislikes))).lstrip(' ')
    except KeyError:
        values['dislikes'] = "N/A"

    try:
        comments = data['statistics']['commentCount']
        values['comments'] = str('{0:20,d}'.format(int(comments))).lstrip(' ')
    except KeyError:
        values['comments'] = "N/A"

    if is_live:
        try:
            values['streamStart'] = arrow.get(data['liveStreamingDetails']['actualStartTime']).humanize()
        except:
            values['streamStart'] = "N/A"

        try:  # Not used currently
            values['streamSchedule'] = arrow.get(data['liveStreamingDetails']['scheduledStartTime']).humanize()
        except:
            values['streamSchedule'] = "N/A"

        try:
            concurrentViewers = data['liveStreamingDetails']['concurrentViewers']
            values['concurrentViewers'] = str('{0:20,d}'.format(int(concurrentViewers))).lstrip(' ')
        except:
            values['concurrentViewers'] = "N/A"

    return values


def get_search_result(api_key, query):
    search_url = "/search?part=id&q={query}" \
                 "&maxResults=1" \
                 "&key={API_KEY}".format(query=query,
                                         API_KEY=api_key)

    endpoint = BASE_URL + search_url

    r = requests.get(endpoint)

    if r.status_code != 200:
        return

    try:
        return r.json()['items'][0]['id']['videoId']
    except:
        return


@commands('yotube', 'yt')
@example('.yt example title')
def youtube_search(bot, trigger):
    query = trigger.group(2)
    video_id = get_search_result(bot.memory['yt_key'], query)
    if not video_id:
        bot.say("[YT Search] Nothing found.")
        return

    values = get_video_info(bot.memory['yt_key'], video_id)
    if not values:
        return

    message = "[YouTube Search] Title: {title} |  " \
              "Uploader: {uploader} | " \
              "Uploaded: {uploaded} | " \
              "Duration: {duration} | " \
              "Views: {views} | " \
              "Likes: {likes} | " \
              "Dislikes: {dislikes} | " \
              "Link: https://youtu.be/{id}".format(**values)

    bot.say(message)

@rule('.*(youtube.com/watch\S*v=|youtu.be/)([\w-]+).*')
def video_info(bot, trigger):
    video_id = trigger.group(2)
    values = get_video_info(bot.memory['yt_key'], video_id)
    if not values:
        return

    if values.get('livestream'):
        message = "[YouTube Livestream] Title: {title} |  " \
                  "Uploader: {uploader} | " \
                  "Stream Started: {streamStart} | " \
                  "Views: {views} | " \
                  "Comments: {comments} | " \
                  "Likes: {likes} | " \
                  "Dislikes: {dislikes}".format(**values)

        if values['concurrentViewers']!="N/A":
            message+=" | {} watching now".format(values['concurrentViewers'])
    else:
        message = "[YouTube] Title: {title} |  " \
                  "Uploader: {uploader} | " \
                  "Uploaded: {uploaded} | " \
                  "Duration: {duration} | " \
                  "Views: {views} | " \
                  "Comments: {comments} | " \
                  "Likes: {likes} | " \
                  "Dislikes: {dislikes}".format(**values)

    bot.say(message)