# -*- coding: utf-8 -*-

# Copyright 2012, Dimitri Molenaars http://tyrope.nl/
# Copyright 2014, Nikola Kovacevic, <nikolak@outlook.com>
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals

import requests
from urllib2 import HTTPError
import re

from lpbot import tools
from lpbot.module import rule, NOLIMIT
from lpbot.logger import get_logger


LOGGER = get_logger(__name__)

issueURL = (r'https?://(?:www\.)?github.com/'
            '([A-z0-9\-]+/[A-z0-9\-]+)/'
            '(?:issues|pull)/'
            '([\d]+)')
regex = re.compile(issueURL)


def checkConfig(bot):
    if not bot.config.has_option('github', 'oauth_token') or not bot.config.has_option('github', 'repo'):
        return False
    else:
        return [bot.config.github.oauth_token, bot.config.github.repo]


def configure(config):
    """
    | [github] | example | purpose |
    | -------- | ------- | ------- |
    | oauth_token | 5868e7af57496cc3ae255868e7af57496cc3ae25 | The OAuth token to connect to your github repo |
    | repo | embolalia/willie | The GitHub repo you're working from. |
    """
    chunk = ''

    if config.option('Configuring github issue reporting and searching module', False):
        config.interactive_add('github', 'oauth_token', 'Github API Oauth2 token', '')
        config.interactive_add('github', 'repo', 'Github repository', 'nikolak/lpbot')

    return chunk


def setup(bot):
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.lpbotMemory()

    bot.memory['url_callbacks'][regex] = issue_info


def shutdown(bot):
    del bot.memory['url_callbacks'][regex]


@rule('.*%s.*' % issueURL)
def issue_info(bot, trigger, match=None):
    match = match or trigger
    URL = 'https://api.github.com/repos/%s/issues/%s' % (match.group(1), match.group(2))

    try:
        raw = requests.get(URL)
    except HTTPError:
        bot.say('The GitHub API returned an error.')

        return NOLIMIT

    data = raw.json()

    try:
        if len(data['body']) == "":
            body = '\x29No description provided.\x29'

            if len(data['body'].split('\n')) > 1:
                body = data['body'].split('\n')[0] + '...'
            else:
                body = data['body'].split('\n')[0]
    except (KeyError):
        bot.say('The API says this is an invalid issue. Please report this if you know it\'s a correct link!')

        return NOLIMIT

    bot.say('%s [#%s] \x02%s |\x02 %s \x02| Status:\x02 %s' % (match.group(1), data['number'], data['title'], body, data['state']))
