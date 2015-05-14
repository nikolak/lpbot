# -*- coding: utf-8 -*-

# Copyright 2009, Silas Baronda
# Copyright 2014, Dimitri Molenaars <tyrope@tyrope.nl>
# Licensed under the Eiffel Forum License 2.

from datetime import datetime
import re
from os import path

import lpbot


log_line = re.compile('\S+ (\S+) (.*? <.*?>) (\d+) (\S+)\tcommit[^:]*: (.+)')


def git_info():
    repo = path.join(path.dirname(path.dirname(path.dirname(__file__))), '.git')
    head = path.join(repo, 'HEAD')
    if path.isfile(head):
        with open(head) as h:
            head_loc = h.readline()[5:-1]  # strip ref: and \n
        head_file = path.join(repo, head_loc)
        if path.isfile(head_file):
            with open(head_file) as h:
                sha = h.readline()
                if sha:
                    return sha


@lpbot.module.commands('version')
def version(bot, trigger):
    """Display the latest commit version, if Willie is running in a git repo."""
    release = lpbot.__version__
    sha = git_info()
    if not sha:
        msg = 'Version: ' + release
        if release[-4:] == '-git':
            msg += ' at unknown commit.'
        bot.reply(msg)
        return

    msg = "Version: {} at commit: {}".format(lpbot.__version__, sha)
    bot.reply(msg + " | GitHub: https://github.com/Nikola-K/lpbot")


@lpbot.module.rule('\x01VERSION\x01')
@lpbot.module.rate(20)
def ctcp_version(bot, trigger):
    bot.write(('NOTICE', trigger.nick),
              '\x01VERSION lpbot IRC Bot version %s\x01' % lpbot.__version__)


@lpbot.module.rule('\x01SOURCE\x01')
@lpbot.module.rate(20)
def ctcp_source(bot, trigger):
    bot.write(('NOTICE', trigger.nick),
              '\x01SOURCE https://github.com/nikola-k/lpbot/\x01')


@lpbot.module.rule('\x01PING\s(.*)\x01')
@lpbot.module.rate(10)
def ctcp_ping(bot, trigger):
    text = trigger.group()
    text = text.replace("PING ", "")
    text = text.replace("\x01", "")
    bot.write(('NOTICE', trigger.nick),
              '\x01PING {0}\x01'.format(text))


@lpbot.module.rule('\x01TIME\x01')
@lpbot.module.rate(20)
def ctcp_time(bot, trigger):
    dt = datetime.now()
    current_time = dt.strftime("%A, %d. %B %Y %I:%M%p")
    bot.write(('NOTICE', trigger.nick),
              '\x01TIME {0}\x01'.format(current_time))
