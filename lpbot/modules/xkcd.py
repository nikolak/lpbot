# -*- coding: utf-8 -*-

# Copyright 2010, Michael Yanovich (yanovich.net), and Morgan Goose
# Copyright 2012, Lior Ramati
# Copyright 2013, Edward Powell (embolalia.com)
# Copyright 2014, Nikola Kovacevic, <nikolak@outlook.com>
# Licensed under the Eiffel Forum License 2.

import random
import re
import requests

from lpbot.module import commands

def get_info(number=None):
    if number:
        url = 'http://xkcd.com/{}/info.0.json'.format(number)
    else:
        url = 'http://xkcd.com/info.0.json'
    data = requests.get(url).json()
    data['url'] = 'http://xkcd.com/' + str(data['num'])
    return data


@commands('xkcd')
def xkcd(bot, trigger):
    """
    .xkcd - Finds an xkcd comic strip. Takes one of 3 inputs:
    If no input is provided it will return a random comic
    If numeric input is provided it will return that comic, or the nth-latest
    comic if the number is non-positive
    If non-numeric input is provided it will return the first google result for those keywords on the xkcd.com site
    """
    # get latest comic for rand function and numeric input
    latest = get_info()
    max_int = latest['num']

    # if no input is given (pre - lior's edits code)
    if not trigger.group(2):  # get rand comic
        random.seed()
        requested = get_info(random.randint(1, max_int + 1))
    else:
        query = trigger.group(2).strip()

        numbered = re.match(r"^(#|\+|-)?(\d+)$", query)
        if numbered:
            query = int(numbered.group(2))
            if numbered.group(1) == "-":
                query = -query
            if query > max_int:
                bot.say(("Sorry, comic #{} hasn't been posted yet. "
                         "The last comic was #{}").format(query, max_int))
                return
            elif query <= -max_int:
                bot.say(("Sorry, but there were only {} comics "
                         "released yet so far").format(max_int))
                return
            elif abs(query) == 0:
                requested = latest
            elif query == 404 or max_int + query == 404:
                bot.say("404 - Not Found")  # don't error on that one
                return
            elif query > 0:
                requested = get_info(query)
            else:
                # Negative: go back that many from current
                requested = get_info(max_int + query)
        else:
            if (query.lower() == "latest" or query.lower() == "newest"):
                requested = latest
            else:
                bot.say("Unknown query")
                return

    message = '{} [{}]'.format(requested['url'], requested['title'])
    bot.say(message)
