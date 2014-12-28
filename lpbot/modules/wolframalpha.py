# -*- coding: utf-8 -*-

# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright 2014, Nikola Kovacevic, <nikolak@outlook.com>
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals

import re
import requests
import urllib
import HTMLParser

from lpbot.module import commands, example


@commands('wa', 'wolfram')
@example('.wa sun mass / earth mass',
         '[wolframalpha] M_sun\/M_earth  (solar mass per Earth mass) = 332948.6')
def wa(bot, trigger):
    """Wolfram Alpha calculator"""
    if not trigger.group(2):
        return bot.reply("No search term.")
    query = trigger.group(2)
    uri = 'http://tumbolia.appspot.com/wa/'

    r = requests.get(uri + urllib.quote(query.replace('+', 'plus'),
                                        "/".encode('utf8')))

    if r.status_code != 200:
        bot.say("[wolframalpha] API did not return good http status")
        return
    else:
        answer = r.content

    if answer:
        answer = answer.decode('unicode_escape')
        answer = HTMLParser.HTMLParser().unescape(answer)
        # This might not work if there are more than one instance of escaped
        # unicode chars But so far I haven't seen any examples of such output
        # examples from Wolfram Alpha
        match = re.search('\\\:([0-9A-Fa-f]{4})', answer)
        if match is not None:
            char_code = match.group(1)
            char = unichr(int(char_code, 16))
            answer = answer.replace('\:' + char_code, char)
        waOutputArray = answer.split(";")
        if (len(waOutputArray) < 2):
            if (answer.strip() == "Couldn't grab results from json stringified precioussss."):
                # Answer isn't given in an IRC-able format, just link to it.
                bot.say(
                    '[wolframalpha]Couldn\'t display answer, try http://www.wolframalpha.com/input/?i=' + query.replace(
                        ' ', '+'))
            else:
                bot.say('[wolframalpha error]' + answer)
        else:

            bot.say('[wolframalpha] ' + waOutputArray[0] + " = "
                    + waOutputArray[1])
        waOutputArray = []
    else:
        bot.reply('Sorry, no result.')


if __name__ == "__main__":
    from lpbot.test_tools import run_example_tests

    run_example_tests(__file__)
