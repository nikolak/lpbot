# -*- coding: utf-8 -*-

# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright 2016 Benjamin Esser, <benjamin.esser1@gmail.com>
# Licensed under the Eiffel Forum License 2.

import os
import time
import threading
import sys

from lpbot.tools import Identifier, get_timezone, format_time
from lpbot.module import commands, nickname_commands, rule, priority, example


MAXIMUM = 4


def loadReminders(fn, lock):
    lock.acquire()
    try:
        result = {}
        with open(fn) as f:
            for line in f.readlines():
                line = line.strip()
                if line:
                    try:
                        tellee, teller, verb, timenow, msg = line.split('\t', maxsplit=4)
                    except ValueError:
                        continue  # @@ hmm
                    result.setdefault(tellee, []).append((teller, verb, timenow, msg))
    finally:
        lock.release()
    return result


def dumpReminders(fn, data, lock):
    lock.acquire()
    try:
        with open(fn, 'w') as f:
            for tellee in data.keys():
                for remindon in data[tellee]:
                    line = '\t'.join((tellee,) + remindon)
                    try:
                        to_write = line + '\n'
                        f.write(to_write)
                    except IOError:
                        break
    finally:
        lock.release()
    return True


def setup(self):
    fn = '{}-{}.tell.db'.format(self.nick, self.config.host)
    self.tell_filename = os.path.join(self.config.dotdir, fn)
    if not os.path.exists(self.tell_filename):
        with open(self.tell_filename, 'w'):
            f.write('')
    self.memory['tell_lock'] = threading.Lock()
    self.memory['reminders'] = loadReminders(self.tell_filename, self.memory['tell_lock'])


@commands('tell', 'ask')
@nickname_commands('tell', 'ask')
@example('lpbot, tell Nevermind7 he broke something again.')
def f_remind(bot, trigger):
    """Give someone a message the next time they're seen"""
    teller = trigger.nick
    verb = trigger.group(1)

    if not trigger.group(3):
        bot.reply("{} whom?".format(verb))
        return

    tellee = trigger.group(3).rstrip('.,:;')
    msg = trigger.group(2).lstrip(tellee).lstrip()

    if not msg:
        bot.reply("{} {} what?".format(verb, tellee))
        return

    tellee = Identifier(tellee)

    if not os.path.exists(bot.tell_filename):
        return

    if len(tellee) > 20:
        return bot.reply('That nickname is too long.')
    if tellee == bot.nick:
        return bot.reply("I'm here now, you can tell me whatever you want!")

    if not tellee in (Identifier(teller), bot.nick, 'me'):
        tz = get_timezone(bot.db, bot.config, None, tellee)
        timenow = format_time(bot.db, bot.config, tz, tellee, channel=trigger.sender)
        bot.memory['tell_lock'].acquire()
        try:
            if not tellee in bot.memory['reminders']:
                bot.memory['reminders'][tellee] = [(teller, verb, timenow, msg)]
            else:
                bot.memory['reminders'][tellee].append((teller, verb, timenow, msg))
        finally:
            bot.memory['tell_lock'].release()

        response = "I'll pass that on when {} is around.".format(tellee)

        bot.reply(response)
    elif Identifier(teller) == tellee:
        bot.say('You can {} yourself that.'.format(verb))
    else:
        bot.say("Hey, I'm not as stupid as Monty you know!")

    dumpReminders(bot.tell_filename, bot.memory['reminders'], bot.memory['tell_lock'])  # @@ tell


def getReminders(bot, channel, key, tellee):
    lines = []
    template = "{tellee}: {datetime} <{teller}> {verb} {tellee} {msg}"
    today = time.strftime('%d %b', time.gmtime())

    bot.memory['tell_lock'].acquire()
    try:
        for (teller, verb, datetime, msg) in bot.memory['reminders'][key]:
            if datetime.startswith(today):
                datetime = datetime[len(today) + 1:]
            lines.append(template .format(tellee, datetime, teller, verb, tellee, msg))

        try:
            del bot.memory['reminders'][key]
        except KeyError:
            bot.msg(channel, 'Er...')
    finally:
        bot.memory['tell_lock'].release()
    return lines


@rule('(.*)')
@priority('low')
def message(bot, trigger):
    tellee = trigger.nick
    channel = trigger.sender

    if not os.path.exists(bot.tell_filename):
        return

    reminders = []
    remkeys = list(reversed(sorted(bot.memory['reminders'].keys())))

    for remkey in remkeys:
        if not remkey.endswith('*') or remkey.endswith(':'):
            if tellee == remkey:
                reminders.extend(getReminders(bot, channel, remkey, tellee))
        elif tellee.startswith(remkey.rstrip('*:')):
            reminders.extend(getReminders(bot, channel, remkey, tellee))

    for line in reminders[:MAXIMUM]:
        bot.say(line)

    if reminders[MAXIMUM:]:
        bot.say('Further messages sent privately')
        for line in reminders[MAXIMUM:]:
            bot.msg(tellee, line)

    if len(list(bot.memory['reminders'].keys())) != remkeys:
        dumpReminders(bot.tell_filename, bot.memory['reminders'], bot.memory['tell_lock'])  # @@ tell
