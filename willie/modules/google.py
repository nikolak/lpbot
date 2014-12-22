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
from collections import OrderedDict

import requests
import urllib
from willie.module import commands, example


def checkConfig(bot):
    if not bot.config.has_option('google', 'cs_id') or \
            not bot.config.has_option('google', 'api_key'):
        return None, None
    else:
        return bot.config.google.cs_id, bot.config.google.api_key


def configure(config):
    """
    | [google] | example | purpose |
    | -------- | ------- | ------- |
    | cs_id | 00436473455324133526:ndsakghasd | Custom search ID |
    | api_key | ASkdasfn3k259283askdhSAT5OADOAKjbh | Custom search API key |
    """
    chunk = ''
    if config.option('Configuring google search module', False):
        config.interactive_add('google', 'cs_id', 'Custom search ID', '')
        config.interactive_add('google', 'api_key', 'Custom search API key', '')
    return chunk

def search_google(query, cs_cx, api_key):
    """
    Searches google for query and returns a string with results.nnnnnnn

    The query can also include additional parameters such as
    "--results int" that specifies number of results to return, must be
    greater than 0 and less than 3. Defaults to 1 if not specified

    And option to modify safe filter with: "--safe str" str being
    "off", "medium", or "high". Defaults to "off" if not specified

    If invalid options are chosen for any of the two parameters they
    are ignored silently.

    Custom search cx and Custom search API key are required for this
    function to work properly.


    Args:
        query - string with search query and (optionally)
                additional search option parameters
        cs_cx - string, Google CS as "{creator}:{id}"
        api_key - string, Google search API key

    Returns:
        String with results formatted as:
            Link title - link url :: link description
        If multiple results are displayed:
            number - link url :: number - link url

            number being the position of the url in the
            results e.g.

            1. outlook.com :: 2. live.com :: etc


    :param query: str
    :param cs_cx: str
    :param api_key: str
    :return:str
    """

    # Initialize default values if no or wrong ones are specified
    # in the query, otherwise use those
    safe = "off"
    r_to_show = 1

    _args = query.split()

    if not _args:
        return "No search query specified"

    if len(_args) >= 3:
        # Additional parameters may be here, if the string is less than 3
        # items long we can be sure it doesn't contain anything additional
        # other than query, since query and one option would be 3 items
        try:
            safe_option_index = _args.index("--safe")
            safe_option_value = _args[safe_option_index + 1]

            _args.pop(safe_option_index)
            _args.pop(safe_option_index)

            if safe_option_value.lower() not in ["off", "medium", "high"]:
                raise ValueError("Invalid value for --safe in google search")

            safe = safe_option_value.lower()
        except:
            pass

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


    # Once we've got all necessary information parsed from query
    # construct URL and parse the data
    params = OrderedDict([
        ('cx', cs_cx),
        ('key', api_key),
        ('rsz', '10'),
        ('num', '10'),
        ('googlehost', 'www.google.com'),
        ('gss', '.com'),
        ('q', query),
        ('oq', query),
        ('filter', '1'),  # duplicate content filter, 1 | 0
        ('safe', safe),  # off | medium | high
    ])

    query_url = 'https://www.googleapis.com/customsearch/v1?{}'.format(
        urllib.urlencode(params))

    r = requests.get(query_url)

    if r.status_code != 200:
        return "Error: Google search failed; status {}".format(r.status_code)

    try:
        gjson = r.json()
    except:
        return "Error: Google did not return a valid json"

    try:
        error = gjson['error']
        return "Google error code: {}, message: {}".format(error['code'],
                                                           error['message'])
    except KeyError:
        pass


    total_results = int(gjson['searchInformation']['totalResults'])

    if total_results == 0:
        return "No results found"

    r_to_show = total_results if total_results < r_to_show else r_to_show

    msg = u"[google] :: "
    if r_to_show == 1:
        result = gjson['items'][0]
        msg += u"{title} - {url} :: {desc}".format(title=result['title'],
                                                  url=result['link'],
                                                  desc=result['snippet'])
    else:
        for i in range(r_to_show):
            result = gjson['items'][i]
            msg += u"{num} - {url} :: ".format(num=i + 1, url=result['link'])

    return msg

@commands('google', 'search', 'g')
@example('.g reddit [--results 3]')
def google(bot, trigger):
    """Replies with search results from Google"""
    cs_cx, api_key = checkConfig(bot)

    if not cs_cx or not api_key:
        return

    query = trigger.group(2)
    try:
        google_result = search_google(query, cs_cx, api_key)
    except:
        google_result = "Error while searching bing"

    bot.reply(google_result)