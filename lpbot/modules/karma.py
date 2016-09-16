# -*- coding: utf-8 -*-

# Copyright 2016, Benjamin Eßer, <benjamin.esser1@gmail.com>

from lpbot.module import commands, OP

def _set_karma(bot, trigger, change, reset=False):
    """Helper function for increasing/decreasing/resetting user karma."""
    channel = trigger.sender
    user = trigger.group(2).split()[0]
    key = '{}_karma'.format(user)
    
    if reset:
        bot.db.set_channel_value(channel, key, 0)
        return
    
    karma = bot.db.get_channel_value(channel, key)
    karma = int(karma) if karma else 0
    if karma or change > 0:
        bot.db.set_channel_value(channel, key, karma + change)
        return karma + change
    else:
        return -1

@commands('upvote')
def upvote(bot, trigger):
    """Give a user karma for being helpful."""
    user = trigger.group(2)
    if not user:
        bot.say(".upvote <nick> - Give <nick> karma for being helpful.")
        return
    if user in (trigger.user, trigger.nick):
        bot.say("Nice try, but you can\'t upvote yourself.")
        return
    karma = _set_karma(bot, trigger, 1)
    bot.say('{}\'s karma increased by 1, {} now has a total karma of {}.'.format(user,
                                                                                 user,
                                                                                 karma))

@commands('downvote')
def downvote(bot, trigger):
    """Substract karma (if karma is positive) from a user for not being helpful."""
    user = trigger.group(2)
    if not user:
        bot.say(".downvote <nick> - Take karma away from <nick>.")
        return
    if user in (trigger.user, trigger.nick):
        bot.say("Why would you downvote yourself? O_o")
        return
    karma = _set_karma(bot, trigger, -1)
    if karma == -1:
        bot.say("{} currently has no karma.".format(user))
        return
    else:
        bot.say("It seems {} wasn\'t very helpful. Karma decreased to {}.".format(user,
                                                                                  karma))

@commands('karma')
def karma(bot, trigger):
    """Report the karma for a user in this channel."""
    user = trigger.group(2).split()[0]
    if not user:
        bot.say(".karma <nick> - Report karma for <nick>.")
        return
    karma = bot.db.get_channel_value(trigger.sender, '{}_karma'.format(user))
    karma = int(karma) if karma else 0
    bot.say('{} has {} karma in {}.'.format(user, karma, trigger.sender))
    
@commands('reset_karma')
def reset_karma(bot, trigger):
    "Reset user karma to 0."
    if bot.privileges[trigger.sender][trigger.nick] < OP:
        return
    user = trigger.group(2)
    if not user:
        bot.say(".reset_karma <nick> - Set <nick>\'s karma to 0.")
        return
    karma = _set_karma(bot, trigger, 0, reset=True)
    bot.say("{}\'s karma reset to 0.".format(user))
