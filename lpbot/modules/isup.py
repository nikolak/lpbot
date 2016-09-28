# -*- coding: utf-8 -*-

# Author: Edward Powell http://embolalia.net
# Copyright 2014, Nikola Kovacevic, <nikolak@outlook.com>
# Copyright 2016, Benjamin Esser, <benjamin.esser1@gmail.com>

import requests

from lpbot.module import commands


@commands('isup')
def isup(bot, trigger):
    """isup.me website status checker"""
    site = trigger.group(2)
    if not site:
        return bot.reply("What site do you want to check?")

    if not site.startswith('http://') and \
	   not site.startswith('https://'):
        if '://' in site:
            protocol = site.split('://')[0] + '://'
            return bot.reply("Try it again without the %s".format(protocol))
        else:
            site = 'http://' + site

    if not '.' in site:
        site += ".com"

    try:
        response = requests.get(site)
    except Exception:
        response = None
        return

    if response:
        bot.say(site + ' looks fine to me.')
    else:
        bot.say(site + ' looks down from here.')
