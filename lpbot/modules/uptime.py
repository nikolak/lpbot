# -*- coding: utf-8 -*-

# Copyright 2014, Fabian Neundorf
# Licensed under the Eiffel Forum License 2.

import datetime

from lpbot.module import commands


def setup(bot):
    if "uptime" not in bot.memory:
        bot.memory["uptime"] = datetime.datetime.utcnow()


@commands('uptime')
def uptime(bot, trigger):
    """.uptime - Returns the uptime of Willie."""
    delta = datetime.timedelta(seconds=round((datetime.datetime.utcnow() -
                                              bot.memory["uptime"])
                                             .total_seconds()))
    bot.say("Current uptime: {}".format(delta))
