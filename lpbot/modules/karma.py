# -*- coding: utf-8 -*-

# Copyright 2016, Benjamin Eßer, <benjamin.esser1@gmail.com>

from lpbot.module import commands

@commands('upvote')
def upvote(bot, trigger):
    """Give a user positive karma for being helpful."""
    if not trigger.group(2):
        bot.say(".upvote <nick> - Give <nick> karma for being helpful.")
        return
    bot.say('Trying to get karma value for user %s in channel %s...' % (trigger.group(2), trigger.sender))
    karma = bot.db.get_channel_value(trigger.sender, trigger.group(2))
    bot.say('Karma for user %s is %s.' % (trigger.group(2), karma))
    bot.db.set_channel_value(trigger.sender, '%s_karma' % trigger.group(2), karma+1)
    bot.say('Added 1 karma to %s, for a total of %s.' % (trigger.group(2), karma+1))
	
@commands('downvote')
def downvote(bot, trigger):
    """Substract karma (if karma is positive) from a user for not being helpful."""
    #TODO check if karma > 0
    if not trigger.group(2):
        bot.say(".downvote <nick> - Take karma away from <nick>.")
        return

@commands('karma')
def karma(bot, trigger):
    """Report the karma for a user in this channel."""
    if not trigger.group(2):
        bot.say(".karma <nick> - Report karma for <nick>.")
        return
    karma = bot.db.get_channel_value(trigger.sender, '%s_karma' % trigger.group(2))
    bot.say('%s has %s karma.' % (trigger.group(2), karma))
