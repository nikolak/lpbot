# -*- coding: utf-8 -*-

# Copyright 2015 Nikola Kovacevic <nikolak@outlook.com>
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

import re

import requests

from lpbot.module import commands, example, NOLIMIT
from lpbot.logger import get_logger

log = get_logger()

regex = re.compile(r'''
    (\d+(?:\.\d+)?)        # Decimal number
    \s*([a-zA-Z]{3})       # 3-letter currency code
    \s+(?:in|as|to)\s+  # preposition
    ([a-zA-Z]{3})          # 3-letter currency code
    ''', re.VERBOSE)


def get_rate(amount, base, symbol):
    API = "https://api.fixer.io/latest?base={base}&symbols={symbol}".format(
        base=base,
        symbol=symbol
    )

    r = requests.get(API, timeout=5)

    if r.status_code != 200:
        try:
            return r.json()['error']
        except Exception as e:
            log.exception(e)
            return "Error occured while fetching data"
    try:
        data = r.json()
    except Exception as e:
        log.exception(e)
        return "Error occured while fetching data"

    if not data.get("rates"):
        return "Unknown currency symbol {}".format(symbol)

    converted = data['rates'][symbol] * amount

    return "{:.2f} {} = {:.2f} {}".format(amount,
                                          base,
                                          converted,
                                          symbol)


@commands('cur', 'currency', 'exchange')
@example('.cur 20 EUR in USD')
def exchange(bot, trigger):
    """Show the exchange rate between two currencies"""
    if not trigger.group(2):
        return bot.reply("No search term. An example: .cur 20 EUR in USD")

    match = regex.match(trigger.group(2))
    if not match:
        bot.reply("Invalid input. Example: .cur 20 eur to usd")
        return NOLIMIT

    amount, base, symbol = match.groups()
    try:
        amount = float(amount)
    except:
        bot.reply("Invalid input. Example: .cur 20 eur to usd")

    bot.say("[Exchange Rate] " + get_rate(amount, base.upper(), symbol.upper()))
