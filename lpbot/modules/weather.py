# -*- coding: utf-8 -*-

# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright 2012, Edward Powell, embolalia.net
# Copyright 2014, Nikola Kovacevic, <nikolak@outlook.com>
# Licensed under the Eiffel Forum License 2.

import urllib.request, urllib.parse, urllib.error
import lxml.etree as etree
import requests

import feedparser

from lpbot.module import commands, example, NOLIMIT


def woeid_search(query):
    """
    Find the first Where On Earth ID for the given query. Result is the etree
    node for the result, so that location data can still be retrieved. Returns
    None if there is no result, or the woeid field is empty.
    """
    query = 'q=select * from geo.placefinder where text="{}"'.format(query)
    r = requests.get('http://query.yahooapis.com/v1/public/yql?' + query)

    if r.status_code == 200:
        body = r.content
    else:
        raise ValueError("API did not return code 200")

    parsed = etree.fromstring(body)
    first_result = parsed.find('results/Result')
    if first_result is None or len(first_result) == 0:
        return None
    return first_result


def get_cover(parsed):
    try:
        condition = parsed.entries[0]['yweather_condition']
    except KeyError:
        return 'unknown'
    text = condition['text']
    # code = int(condition['code'])
    # TODO parse code to get those little icon thingies.
    return text


def get_temp(parsed):
    try:
        condition = parsed.entries[0]['yweather_condition']
        temp = int(condition['temp'])
    except (KeyError, ValueError):
        return 'unknown'
    f = round((temp * 1.8) + 32, 2)
    return ('%d\u00B0C (%d\u00B0F)' % (temp, f))


def get_humidity(parsed):
    try:
        humidity = parsed['feed']['yweather_atmosphere']['humidity']
    except (KeyError, ValueError):
        return 'unknown'
    return "Humidity: %s%%" % humidity


def get_wind(parsed):
    try:
        wind_data = parsed['feed']['yweather_wind']
        kph = float(wind_data['speed'])
        m_s = float(round(kph / 3.6, 1))
        speed = int(round(kph / 1.852, 0))
        degrees = int(wind_data['direction'])
    except (KeyError, ValueError):
        return 'unknown'

    if speed < 1:
        description = 'Calm'
    elif speed < 4:
        description = 'Light air'
    elif speed < 7:
        description = 'Light breeze'
    elif speed < 11:
        description = 'Gentle breeze'
    elif speed < 16:
        description = 'Moderate breeze'
    elif speed < 22:
        description = 'Fresh breeze'
    elif speed < 28:
        description = 'Strong breeze'
    elif speed < 34:
        description = 'Near gale'
    elif speed < 41:
        description = 'Gale'
    elif speed < 48:
        description = 'Strong gale'
    elif speed < 56:
        description = 'Storm'
    elif speed < 64:
        description = 'Violent storm'
    else:
        description = 'Hurricane'

    if (degrees <= 22.5) or (degrees > 337.5):
        degrees = '\u2191'
    elif (degrees > 22.5) and (degrees <= 67.5):
        degrees = '\u2197'
    elif (degrees > 67.5) and (degrees <= 112.5):
        degrees = '\u2192'
    elif (degrees > 112.5) and (degrees <= 157.5):
        degrees = '\u2198'
    elif (degrees > 157.5) and (degrees <= 202.5):
        degrees = '\u2193'
    elif (degrees > 202.5) and (degrees <= 247.5):
        degrees = '\u2199'
    elif (degrees > 247.5) and (degrees <= 292.5):
        degrees = '\u2190'
    elif (degrees > 292.5) and (degrees <= 337.5):
        degrees = '\u2196'

    return description + ' ' + str(m_s) + 'm/s (' + degrees + ')'


@commands('weather', 'wea')
@example('.weather London')
def weather(bot, trigger):
    """.weather location - Show the weather at the given location."""

    location = trigger.group(2)
    woeid = ''
    if not location:
        woeid = bot.db.get_nick_value(trigger.nick, 'woeid')
        if not woeid:
            return bot.msg(trigger.sender, "I don't know where you live. " +
                           'Give me a location, like .weather London, or tell me where you live by saying .setlocation London, for example.')
    else:
        location = location.strip()
        first_result = woeid_search(location)
        if first_result is not None:
            woeid = first_result.find('woeid').text

    if not woeid:
        return bot.reply("I don't know where that is.")

    query = urllib.parse.urlencode({'w': woeid, 'u': 'c'})
    url = 'http://weather.yahooapis.com/forecastrss?' + query
    parsed = feedparser.parse(url)
    location = parsed['feed']['title']
    additional_data = [
        get_cover(parsed),
        get_temp(parsed),
        get_humidity(parsed),
        get_wind(parsed)]
    bot.say('{}: {}'.format(location, ", ".join(additional_data)))


@commands('setlocation', 'setwoeid')
@example('.setlocation Columbus, OH')
def update_woeid(bot, trigger):
    """Set your default weather location."""
    if not trigger.group(2):
        bot.reply('Give me a location, like "Washington, DC" or "London".')
        return NOLIMIT

    first_result = woeid_search(trigger.group(2))
    if first_result is None:
        return bot.reply("I don't know where that is.")

    try:
        woeid = first_result.find('woeid').text

        if not woeid:
            raise ValueError("Invalid WOEID")
    except:
        bot.reply("Could not get a valid WOEID for that location")
        return

    bot.db.set_nick_value(trigger.nick, 'woeid', woeid)

    response_data = []
    for property in ['neighborhood', 'city', 'state', 'country', 'uzip']:
        try:
            value = first_result.find(property).text
            if value:
                response_data.append(value)
        except:
            pass

    bot.reply("Location set to: WOEID {} ({})".format(woeid,
                                                      ", ".join(response_data))
    )
