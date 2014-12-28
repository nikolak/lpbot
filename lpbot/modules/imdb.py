# -*- coding: utf-8 -*-

# Original code copyright:
# Copyright © 2012-2013, Elad Alfassa, <elad@fedoraproject.org>
# Copyright 2014, Nikola Kovacevic, <nikolak@outlook.com>
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals
import requests

import lpbot.module
from lpbot.logger import get_logger


LOGGER = get_logger(__name__)


@lpbot.module.commands('imdb')
@lpbot.module.example('.imbd ThisTitleDoesNotExist', '[IMDb] Movie not found!')
@lpbot.module.example('.imdb Citizen Kane',
                      '[IMDb] Title: Citizen Kane | Year: 1941 | Rating: 8.4 | Genre: Drama, Mystery | IMDB Link: http://imdb.com/title/tt0033467')
def imdb(bot, trigger):
    """
    Returns some information about a movie, like Title, Year, Rating, Genre and IMDB Link.
    """
    if not trigger.group(2):
        return
    word = trigger.group(2).rstrip()
    uri = "http://www.imdbapi.com/?t=" + word
    r = requests.get(uri)

    if not r.status_code == 200:
        bot.say("Could not get a response from the API")
        return

    data = r.json()
    if data['Response'] == 'False':
        if 'Error' in data:
            message = '[IMDb] %s' % data['Error']
        else:
            LOGGER.warning(
                'Got an error from the imdb api, search phrase was %s; data was %s',
                word, str(data))
            message = '[IMDb] Got an error from imdbapi'
    else:
        message = '[IMDb] Title: ' + data['Title'] + \
                  ' | Year: ' + data['Year'] + \
                  ' | Rating: ' + data['imdbRating'] + \
                  ' | Genre: ' + data['Genre'] + \
                  ' | IMDb Link: http://imdb.com/title/' + data['imdbID']
    bot.say(message)
