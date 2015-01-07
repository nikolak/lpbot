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

from __future__ import unicode_literals
from lpbot.module import commands, example, NOLIMIT

from dateutil.tz import tzoffset
from datetime import datetime



@commands('date')
@example('.date [utc offset]')
def date(bot, trigger):
    offset = trigger.group(2)

    if not offset:
        offset = 0
    elif offset and offset.isdigit():
        offset = offset * 60 * 60
    else:
        bot.say("Please use correct format: .date -6")

    bot.reply(datetime.now(tzoffset("offset", offset)))