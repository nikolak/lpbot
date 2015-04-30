# -*- coding: utf-8 -*-

# Copyright 2010-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich
# (yanovich.net)
# Copyright © 2012, Elad Alfassa, <elad@fedoraproject.org>
# Copyright 2013, Ari Koivula <ari@koivu.la>
# Copyright 2014, Nikola Kovacevic, <nikolak@outlook.com>
# Licensed under the Eiffel Forum License 2.


from lpbot.module import commands, priority, example, event, rule
from lpbot.tools import owner_only


def configure(config):
    """
    | [admin] | example | purpose |
    | -------- | ------- | ------- |
    | hold_ground | False | Auto re-join on kick |
    | owner_pass | string | Password for identifying owner |
    """
    config.add_option('admin', 'hold_ground', "Auto re-join on kick")
    config.add_option('admin', 'owner_pass', "Password for identifying owner")

@owner_only
@commands('join')
@priority('low')
@example('.join #example or .join #example key')
def join(bot, trigger):
    """Join the specified channel. This is an admin-only command."""
    # Can only be done in privmsg by an admin
    if not trigger.is_privmsg:
        return

    if trigger.admin:
        channel, key = trigger.group(3), trigger.group(4)
        if not channel:
            return
        elif not key:
            bot.join(channel)
        else:
            bot.join(channel, key)

@owner_only
@commands('part')
@priority('low')
@example('.part #example')
def part(bot, trigger):
    """Part the specified channel. This is an admin-only command."""
    # Can only be done in privmsg by an admin
    if not trigger.is_privmsg:
        return
    if not trigger.admin:
        return

    channel, _sep, part_msg = trigger.group(2).partition(' ')
    if part_msg:
        bot.part(channel, part_msg)
    else:
        bot.part(channel)

@owner_only
@commands('quit')
@priority('low')
def quit(bot, trigger):
    """Quit from the server. This is an owner-only command."""
    # Can only be done in privmsg by the owner
    if not trigger.is_privmsg:
        return
    if not trigger.owner:
        return

    quit_message = trigger.group(2)
    if not quit_message:
        quit_message = 'Quitting on command from %s' % trigger.nick

    bot.quit(quit_message)

@owner_only
@commands('msg')
@priority('low')
@example('.msg #YourPants Does anyone else smell neurotoxin?')
def msg(bot, trigger):
    """
    Send a message to a given channel or nick. Can only be done in privmsg by an
    admin.
    """
    if not trigger.is_privmsg:
        return
    if not trigger.admin:
        return
    if trigger.group(2) is None:
        return

    channel, _sep, message = trigger.group(2).partition(' ')
    message = message.strip()
    if not channel or not message:
        return

    bot.msg(channel, message)

@owner_only
@commands('me')
@priority('low')
def me(bot, trigger):
    """
    Send an ACTION (/me) to a given channel or nick. Can only be done in privmsg
    by an admin.
    """
    if not trigger.is_privmsg:
        return
    if not trigger.admin:
        return
    if trigger.group(2) is None:
        return

    channel, _sep, action = trigger.group(2).partition(' ')
    action = action.strip()
    if not channel or not action:
        return

    msg = '\x01ACTION %s\x01' % action
    bot.msg(channel, msg)


@event('INVITE')
@rule('.*')
@priority('low')
def invite_join(bot, trigger):
    """
    Join a channel lpbot is invited to, if the inviter is an admin.
    """
    if not trigger.admin:
        return
    bot.join(trigger.args[1])


@event('KICK')
@rule(r'.*')
@priority('low')
def hold_ground(bot, trigger):
    """
    This function monitors all kicks across all channels lpbot is in. If it
    detects that it is the one kicked it'll automatically join that channel.

    WARNING: This may not be needed and could cause problems if lpbot becomes
    annoying. Please use this with caution.
    """
    if bot.config.has_section('admin') and bot.config.admin.hold_ground:
        channel = trigger.sender
        if trigger.args[1] == bot.nick:
            bot.join(channel)

@owner_only
@commands('mode')
@priority('low')
def mode(bot, trigger):
    """Set a user mode on lpbot. Can only be done in privmsg by an admin."""
    if not trigger.is_privmsg:
        return
    if not trigger.admin:
        return
    mode = trigger.group(3)
    bot.write(('MODE ', bot.nick + ' ' + mode))

@owner_only
@commands('set')
@example('.set core.owner Me')
def set_config(bot, trigger):
    """See and modify values of lpbots config object.

    Trigger args:
        arg1 - section and option, in the form "section.option"
        arg2 - value

    If there is no section, section will default to "core".
    If value is None, the option will be deleted.
    """
    if not trigger.is_privmsg:
        bot.reply("This command only works as a private message.")
        return
    if not trigger.admin:
        bot.reply("This command requires admin priviledges.")
        return

    # Get section and option from first argument.
    arg1 = trigger.group(3).split('.')
    if len(arg1) == 1:
        section, option = "core", arg1[0]
    elif len(arg1) == 2:
        section, option = arg1
    else:
        bot.reply("Usage: .set section.option value")
        return

    # Display current value if no value is given.
    value = trigger.group(4)
    if not value:
        if not bot.config.has_option(section, option):
            bot.reply("Option %s.%s does not exist." % (section, option))
            return
        # Except if the option looks like a password. Censor those to stop them
        # from being put on log files.
        if option.endswith("password") or option.endswith("pass"):
            value = "(password censored)"
        else:
            value = getattr(getattr(bot.config, section), option)
        bot.reply("%s.%s = %s" % (section, option, value))
        return

    # Otherwise, set the value to one given as argument 2.
    setattr(getattr(bot.config, section), option, value)

@owner_only
@commands('ignore')
@example('.ignore MysteriousMagent')
def ignore_user(bot, trigger):
    if not trigger.is_privmsg:
        bot.reply("This command only works as a private message.")
        return
    if not trigger.admin:
        bot.reply("This command requires admin priviledges.")
        return

    if bot.config.has_option('core', 'nick_blocks'):
        current_blocks = bot.config.core.nick_blocks
    else:
        current_blocks = []

    if not current_blocks:
        current_blocks = []

    user_to_ignore = trigger.group(2)
    if user_to_ignore in current_blocks:
        bot.reply("User {} is already being ignored".format(user_to_ignore))
        return

    current_blocks.append(user_to_ignore.lower())

    setattr(getattr(bot.config, 'core'), 'nick_blocks', ','.join(current_blocks))
    bot.reply("User {} added to ignore block".format(user_to_ignore))

@owner_only
@commands("unignore")
@example('.unignore someone')
def unignore_user(bot, trigger):
    if not trigger.is_privmsg:
        bot.reply("This command only works as a private message.")
        return
    if not trigger.admin:
        bot.reply("This command requires admin priviledges.")
        return

    if bot.config.has_option('core', 'nick_blocks'):
        current_blocks = bot.config.core.nick_blocks
    else:
        bot.reply("There are no active nick blocks")
        return

    if not current_blocks:
        bot.reply("There are no active nick blocks")
        return

    nickname = trigger.group(2)

    if nickname.lower() not in current_blocks:
        bot.reply("That username is not ignored")
        return

    current_blocks.remove(nickname.lower())

    setattr(getattr(bot.config, 'core'), 'nick_blocks', ','.join(current_blocks))
    bot.reply("User {} removed from ignore list".format(nickname))


@commands('save')
@example('.save')
@owner_only
def save_config(bot, trigger):
    """Save state of lpbots config object to the configuration file."""
    if not trigger.is_privmsg:
        return
    if not trigger.admin:
        return
    bot.config.save()

@commands('identify')
def auth_owner(bot, trigger):
    print(trigger.admin)
    if trigger.nick != bot.config.core.owner:
        return
    if not trigger.is_privmsg:
        return

    if trigger.group(2) == bot.config.admin.owner_pass:
        bot.say("Logged in as owner!")
        bot.memory['owner_auth'] = True

@commands("amiowner")
@owner_only
def amiowner(bot, trigger):
    bot.say("You are currently identified as owner.")