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

from __future__ import unicode_literals

import requests
from willie.module import commands, example


def checkConfig(bot):
    if not bot.config.has_option('bing', 'api_key'):
        return False
    else:
        return bot.config.bing.api_key


def configure(config):
    """
    | [bing  ] | example | purpose |
    | -------- | ------- | ------- |
    | api_key | VBsdaiY23sdcxuNG1gP+YBsCwJxzjfHgdsXJG5 | Bing Primary Account Key |
    """
    chunk = ''
    if config.option('Configuring bing search module', False):
        config.interactive_add('bing', 'api_key', 'Bing Primary Account Key', '')
    return chunk


def search_bing(query, api_key, search_type="Web"):
    api_base = "https://api.datamarket.azure.com/Bing/Search/v1/"
    api_query = "{s_type}?Query='{query}'&$format=json&$top={results}"

    results = 1
    request_keymap = {"'": '%27',
                      '"': '%27',
                      '+': '%2b',
                      ' ': '%20',
                      ':': '%3a', }

    if not query:
        return "No query specified"

    if query.find("results") != -1:
        r_index = query.find("results")
        r_string = query[r_index - 2:r_index].rstrip()

        try:
            r_string = int(r_string)
            if r_string < 1 or r_string > 3:
                raise ValueError

            results = r_string
            query = query.replace("{} results".format(results), "")
        except ValueError:
            pass

    query_url = api_query.format(s_type=search_type, query=query, results=results)

    for key, value in request_keymap.items():
        query_url = query_url.replace(key, value)

    r = requests.get(api_base + query_url, auth=(api_key, api_key))

    search_results = None
    if r.status_code == 200:
        try:
            search_results = r.json()['d']['results']
        except:
            return "Something went wrong while converting result to json"

    if not search_results:
        return "[bing] :: Nothing found"

    message = u"[bing] :: "
    if results > 1:
        for num in range(results):
            try:
                message += u"{} - {} :: ".format(num + 1, search_results[num]['Url'])
            except:
                message += u"{} - Not found :: ".format(num + 1)
    else:
        message += u"{} - {} :: {}".format(search_results[0]['Title'],
                                           search_results[0]['Url'],
                                           search_results[0]['Description'])

    return message


@commands('bing', 'search', 'b')
@example('.bing microsoft windows')
def bing(bot, trigger):
    """Replies with results from bing API"""
    api_key = checkConfig(bot)

    query = trigger.group(2)
    try:
        bing_result = search_bing(query, api_key)
    except:
        bing_result = "Error while searching bing"

    bot.reply(bing_result)