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
# Original code copyright:
# Copyright © 2012-2013, Elad Alfassa, <elad@fedoraproject.org>
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals
import json
import willie.web as web
import willie.module
from willie.logger import get_logger

LOGGER = get_logger(__name__)


@willie.module.commands('imbd')
@willie.module.example('.imbd ThisTitleDoesNotExist', '[IMDb] Movie not found!')
@willie.module.example('.imdb Citizen Kane', '[IMDb] Title: Citizen Kane | Year: 1941 | Rating: 8.4 | Genre: Drama, Mystery | IMDB Link: http://imdb.com/title/tt0033467')
def imdb(bot, trigger):
    """
    Returns some information about a movie, like Title, Year, Rating, Genre and IMDB Link.
    """
    if not trigger.group(2):
        return
    word = trigger.group(2).rstrip()
    uri = "http://www.imdbapi.com/?t=" + word
    u = web.get(uri, 30)
    data = json.loads(u)  # data is a Dict containing all the information we need
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


if __name__ == "__main__":
    from willie.test_tools import run_example_tests
    run_example_tests(__file__)
