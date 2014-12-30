import time

from lpbot.module import commands, example, NOLIMIT

@commands('date')
@example('.date')
def date(bot, trigger):
    print(time.strftime("%H:%M:%S"))