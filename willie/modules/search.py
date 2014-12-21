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
#
# # Original code copyright:
# Copyright 2008-9, Sean B. Palmer, inamidst.com
# Copyright 2012, Edward Powell, embolalia.net
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals

import re
from willie import web
from willie.module import commands, example
import json


def formatnumber(n):
    """Format a number with beautiful commas."""
    parts = list(str(n))
    for i in range((len(parts) - 3), 0, -3):
        parts.insert(i, ',')
    return ''.join(parts)


r_bing = re.compile(r'<h3><a href="([^"]+)"')

#fixme
def bing_search(query, lang='en-GB'):
    base = 'http://www.bing.com/search?mkt=%s&q=' % lang
    bytes = web.get(base + query)
    m = r_bing.search(bytes)
    if m:
        return m.group(1)


r_duck = re.compile(r'nofollow" class="[^"]+" href="(.*?)">')


def duck_search(query):
    query = query.replace('!', '')
    uri = 'http://duckduckgo.com/html/?q=%s&kl=uk-en' % query
    bytes = web.get(uri)
    if 'web-result"' in bytes:  # filter out the adds on top of the page
        bytes = bytes.split('web-result"')[1]
    m = r_duck.search(bytes)
    if m:
        return web.decode(m.group(1))

# Alias google_search to duck_search
google_search = duck_search


def duck_api(query):
    if '!bang' in query.lower():
        return 'https://duckduckgo.com/bang.html'

    uri = 'http://api.duckduckgo.com/?q=%s&format=json&no_html=1&no_redirect=1' % query
    results = json.loads(web.get(uri))
    if results['Redirect']:
        return results['Redirect']
    else:
        return None


@commands('duck', 'ddg', 'g')
@example('.duck privacy or .duck !mcwiki obsidian')
def duck(bot, trigger):
    """Queries Duck Duck Go for the specified input."""
    query = trigger.group(2)
    if not query:
        return bot.reply('.ddg what?')

    # If the API gives us something, say it and stop
    result = duck_api(query)
    if result:
        bot.reply(result)
        return

    # Otherwise, look it up on the HTMl version
    uri = duck_search(query)

    if uri:
        bot.reply(uri)
        if 'last_seen_url' in bot.memory:
            bot.memory['last_seen_url'][trigger.sender] = uri
    else:
        bot.reply("No results found for '%s'." % query)

# FIXME
# @commands("bing")
# @example(".bing download linux")
# def bing(bot, trigger):
#     query = trigger.group(2)
#
#     if not query:
#         return bot.reply("Search bing for what?")
#
#     bing_result = bing_search(query)
#
#     if bing_result:
#         bot.reply(bing_result)
#         return
#     else:
#         bot.reply("Could not find any results on bing for {}".format(query))
#

@commands('search')
@example('.search nerdfighter')
def search(bot, trigger):
    """Searches Bing and Duck Duck Go."""
    if not trigger.group(2):
        return bot.reply('.search for what?')
    query = trigger.group(2)

    ddg_result = duck_search(query) or '-'
    if ddg_result:
        bot.reply(ddg_result)
    else:
        bot.reply("No results found on duckduck go for {}".format(query))

@commands('suggest')
def suggest(bot, trigger):
    """Suggest terms starting with given input"""
    if not trigger.group(2):
        return bot.reply("No query term.")
    query = trigger.group(2)
    uri = 'http://websitedev.de/temp-bin/suggest.pl?q='
    answer = web.get(uri + query.replace('+', '%2B'))
    if answer:
        bot.say(answer)
    else:
        bot.reply('Sorry, no result.')
