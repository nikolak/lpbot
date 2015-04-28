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

import requests

from lpbot.module import commands, example


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

    r_to_show = 1
    request_keymap = {"'": '%27',
                      '"': '%27',
                      '+': '%2b',
                      ' ': '%20',
                      ':': '%3a', }

    _args = query.split()

    if not _args:
        return "No search query specified"

    if len(_args) >= 3:
        # Additional parameters may be here, if the string is less than 3
        # items long we can be sure it doesn't contain anything additional
        # other than query, since query and one option would be 3 items
        try:
            results_number_index = _args.index("--results")
            results_number_value = _args[results_number_index + 1]

            _args.pop(results_number_index)
            _args.pop(results_number_index)

            results_number_value = int(results_number_value)

            if results_number_value < 1 or results_number_value > 3:
                raise ValueError("Invalid value for --results, n<1 or n>3")

            r_to_show = results_number_value
        except:
            pass

    query = " ".join(_args)

    query_url = api_query.format(s_type=search_type, query=query, results=r_to_show)

    for key, value in request_keymap.items():
        query_url = query_url.replace(key, value)

    r = requests.get(api_base + query_url, auth=(api_key, api_key))

    if r.status_code != 200:
        return "Error: Bing search failed; status {}".format(r.status_code)

    try:
        bjson = r.json()['d']['results']
    except:
        return "Error: Bing did not return a valid json"

    if not bjson:
        return "Nothing found"

    msg = u"[bing] :: "
    if r_to_show == 1:
        result = bjson[0]
        msg += u"{title} - {url} :: {desc}".format(title=result['Title'],
                                                   url=result['Url'],
                                                   desc=result['Description'])
    else:
        for i in range(r_to_show):
            result = bjson[i]
            msg += u"{num} - {url} :: ".format(num=i + 1, url=result['Url'])

    return msg


@commands('bing', 'b')
@example('.bing microsoft windows [--results 3]')
def bing(bot, trigger):
    """Replies with results from bing API"""
    api_key = checkConfig(bot)

    if not api_key:
        return

    query = trigger.group(2)
    try:
        bing_result = search_bing(query, api_key)
    except:
        bing_result = "Error while searching bing"

    bot.reply(bing_result)