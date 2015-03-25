# -*- coding: utf-8 -*-

# Copyright 2008-2011, Sean B. Palmer (inamidst.com) and Michael Yanovich
# (yanovich.net)
# Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
# Copyright 2012, Edward Powell (embolalia.net)
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals

import re
import time
import base64

import lpbot
from lpbot.tools import Identifier, iteritems
from lpbot.logger import get_logger


LOGGER = get_logger(__name__)


@lpbot.module.event('001', '251')
@lpbot.module.rule('.*')
@lpbot.module.thread(False)
@lpbot.module.unblockable
def startup(bot, trigger):
    """Do tasks related to connecting to the network.

    001 RPL_WELCOME is from RFC2812 and is the first message that is sent after
    the connection has been registered on the network.

    251 RPL_LUSERCLIENT is a mandatory message that is sent after client
    connects to the server in rfc1459. RFC2812 does not require it and all
    networks might not send it. We support both.

    """
    if bot.connection_registered:
        return

    bot.connection_registered = True

    if bot.config.core.nickserv_password is not None:
        bot.msg(
            'NickServ',
            'IDENTIFY %s' % bot.config.core.nickserv_password
        )

    if (bot.config.core.oper_name is not None
        and bot.config.core.oper_password is not None):
        bot.write((
            'OPER',
            bot.config.core.oper_name + ' ' + bot.config.oper_password
        ))

    # Use Authserv if authserv_password and authserv_account is set in config.
    if (bot.config.core.authserv_password is not None
        and bot.config.core.authserv_account is not None):
        bot.write((
            'AUTHSERV auth',
            bot.config.core.authserv_account + ' ' + bot.config.authserv_password
        ))

    #Set bot modes per config, +B if no config option is defined
    if bot.config.has_option('core', 'modes'):
        modes = bot.config.core.modes
    else:
        modes = 'B'
    bot.write(('MODE ', '%s +%s' % (bot.nick, modes)))

    bot.memory['retry_join'] = dict()

    if bot.config.has_option('core', 'throttle_join'):
        throttle_rate = int(bot.config.core.throttle_join)
        channels_joined = 0
        for channel in bot.config.core.get_list('channels'):
            channels_joined += 1
            if not channels_joined % throttle_rate:
                time.sleep(1)
            bot.join(channel)
    else:
        for channel in bot.config.core.get_list('channels'):
            bot.join(channel)


@lpbot.module.event('477')
@lpbot.module.rule('.*')
@lpbot.module.priority('high')
def retry_join(bot, trigger):
    """Give NickServer enough time to identify on a +R channel.

    Give NickServ enough time to identify, and retry rejoining an
    identified-only (+R) channel. Maximum of ten rejoin attempts.

    """
    channel = trigger.args[1]
    if channel in bot.memory['retry_join'].keys():
        bot.memory['retry_join'][channel] += 1
        if bot.memory['retry_join'][channel] > 10:
            LOGGER.warning('Failed to join %s after 10 attempts.', channel)
            return
    else:
        bot.memory['retry_join'][channel] = 0
        bot.join(channel)
        return

    time.sleep(6)
    bot.join(channel)


# Functions to maintain a list of chanops in all of lpbot's channels.


@lpbot.module.rule('(.*)')
@lpbot.module.event('353')
@lpbot.module.priority('high')
@lpbot.module.thread(False)
@lpbot.module.unblockable
def handle_names(bot, trigger):
    """Handle NAMES response, happens when joining to channels."""
    names = trigger.split()

    #TODO specific to one channel type. See issue 281.
    channels = re.search('(#\S*)', trigger.raw)
    if not channels:
        return
    channel = Identifier(channels.group(1))
    if channel not in bot.privileges:
        bot.privileges[channel] = dict()
    bot.init_ops_list(channel)

    # This could probably be made flexible in the future, but I don't think
    # it'd be worth it.
    mapping = {'+': lpbot.module.VOICE,
               '%': lpbot.module.HALFOP,
               '@': lpbot.module.OP,
               '&': lpbot.module.ADMIN,
               '~': lpbot.module.OWNER}

    for name in names:
        priv = 0
        for prefix, value in iteritems(mapping):
            if prefix in name:
                priv = priv | value
        nick = Identifier(name.lstrip(''.join(mapping.keys())))
        bot.privileges[channel][nick] = priv

        # Old op list maintenance is down here, and should be removed at some
        # point
        if '@' in name or '~' in name or '&' in name:
            bot.add_op(channel, name.lstrip('@&%+~'))
            bot.add_halfop(channel, name.lstrip('@&%+~'))
            bot.add_voice(channel, name.lstrip('@&%+~'))
        elif '%' in name:
            bot.add_halfop(channel, name.lstrip('@&%+~'))
            bot.add_voice(channel, name.lstrip('@&%+~'))
        elif '+' in name:
            bot.add_voice(channel, name.lstrip('@&%+~'))


@lpbot.module.rule('(.*)')
@lpbot.module.event('MODE')
@lpbot.module.priority('high')
@lpbot.module.thread(False)
@lpbot.module.unblockable
def track_modes(bot, trigger):
    """Track usermode changes and keep our lists of ops up to date."""
    # Mode message format: <channel> *( ( "-" / "+" ) *<modes> *<modeparams> )
    channel = Identifier(trigger.args[0])
    line = trigger.args[1:]

    # If the first character of where the mode is being set isn't a #
    # then it's a user mode, not a channel mode, so we'll ignore it.
    if channel.is_nick():
        return

    def handle_old_modes(nick, mode):
        #Old mode maintenance. Drop this crap in 5.0.
        if mode[1] == 'o' or mode[1] == 'q' or mode[1] == 'a':
            if mode[0] == '+':
                bot.add_op(channel, nick)
            else:
                bot.del_op(channel, nick)
        elif mode[1] == 'h':  # Halfop
            if mode[0] == '+':
                bot.add_halfop(channel, nick)
            else:
                bot.del_halfop(channel, nick)
        elif mode[1] == 'v':
            if mode[0] == '+':
                bot.add_voice(channel, nick)
            else:
                bot.del_voice(channel, nick)

    mapping = {'v': lpbot.module.VOICE,
               'h': lpbot.module.HALFOP,
               'o': lpbot.module.OP,
               'a': lpbot.module.ADMIN,
               'q': lpbot.module.OWNER}

    modes = []
    for arg in line:
        if len(arg) == 0:
            continue
        if arg[0] in '+-':
            # There was a comment claiming IRC allows e.g. MODE +aB-c foo, but
            # I don't see it in any RFCs. Leaving in the extra parsing for now.
            sign = ''
            modes = []
            for char in arg:
                if char == '+' or char == '-':
                    sign = char
                else:
                    modes.append(sign + char)
        else:
            arg = Identifier(arg)
            for mode in modes:
                priv = bot.privileges[channel].get(arg, 0)
                value = mapping.get(mode[1])
                if value is not None:
                    if mode[0] == '+':
                        priv = priv | value
                    else:
                        priv = priv & ~value
                    bot.privileges[channel][arg] = priv
                handle_old_modes(arg, mode)


@lpbot.module.rule('.*')
@lpbot.module.event('NICK')
@lpbot.module.priority('high')
@lpbot.module.thread(False)
@lpbot.module.unblockable
def track_nicks(bot, trigger):
    """Track nickname changes and maintain our chanops list accordingly."""
    old = trigger.nick
    new = Identifier(trigger)

    # Give debug mssage, and PM the owner, if the bot's own nick changes.
    if old == bot.nick:
        privmsg = "Hi, I'm your bot, %s." + \
                  " Something has made my nick change." + \
                  " This can cause some problems for me," + \
                  " and make me do weird things." + \
                  " You'll probably want to restart me," + \
                  " and figure out what made that happen" + \
                  " so you can stop it happening again." + \
                  " (Usually, it means you tried to give me a nick" + \
                  " that's protected by NickServ.)" % bot.nick
        debug_msg = "Nick changed by server." + \
                    " This can cause unexpected behavior. Please restart the bot."
        LOGGER.critical(debug_msg)
        bot.msg(bot.config.core.owner, privmsg)
        return

    for channel in bot.privileges:
        channel = Identifier(channel)
        if old in bot.privileges[channel]:
            value = bot.privileges[channel].pop(old)
            bot.privileges[channel][new] = value

    # Old privilege maintenance
    for channel in bot.halfplus:
        if old in bot.halfplus[channel]:
            bot.del_halfop(channel, old)
            bot.add_halfop(channel, new)
    for channel in bot.ops:
        if old in bot.ops[channel]:
            bot.del_op(channel, old)
            bot.add_op(channel, new)
    for channel in bot.voices:
        if old in bot.voices[channel]:
            bot.del_voice(channel, old)
            bot.add_voice(channel, new)


@lpbot.module.rule('(.*)')
@lpbot.module.event('PART')
@lpbot.module.priority('high')
@lpbot.module.thread(False)
@lpbot.module.unblockable
def track_part(bot, trigger):
    if trigger.nick == bot.nick:
        bot.channels.remove(trigger.sender)
        del bot.privileges[trigger.sender]
    else:
        try:
            del bot.privileges[trigger.sender][trigger.nick]
        except KeyError:
            pass


@lpbot.module.rule('.*')
@lpbot.module.event('KICK')
@lpbot.module.priority('high')
@lpbot.module.thread(False)
@lpbot.module.unblockable
def track_kick(bot, trigger):
    nick = Identifier(trigger.args[1])
    if nick == bot.nick:
        bot.channels.remove(trigger.sender)
        del bot.privileges[trigger.sender]
    else:
        # Temporary fix to stop KeyErrors from being sent to channel
        # The privileges dict may not have all nicks stored at all times
        # causing KeyErrors
        try:
            del bot.privileges[trigger.sender][nick]
        except KeyError:
            pass


@lpbot.module.rule('.*')
@lpbot.module.event('JOIN')
@lpbot.module.priority('high')
@lpbot.module.thread(False)
@lpbot.module.unblockable
def track_join(bot, trigger):
    if trigger.nick == bot.nick and trigger.sender not in bot.channels:
        bot.channels.append(trigger.sender)
        bot.privileges[trigger.sender] = dict()
    bot.privileges[trigger.sender][trigger.nick] = 0


@lpbot.module.rule('.*')
@lpbot.module.event('QUIT')
@lpbot.module.priority('high')
@lpbot.module.thread(False)
@lpbot.module.unblockable
def track_quit(bot, trigger):
    for chanprivs in bot.privileges.values():
        if trigger.nick in chanprivs:
            del chanprivs[trigger.nick]


@lpbot.module.rule('.*')
@lpbot.module.event('CAP')
@lpbot.module.thread(False)
@lpbot.module.priority('high')
@lpbot.module.unblockable
def recieve_cap_list(bot, trigger):
    # Server is listing capabilites
    if trigger.args[1] == 'LS':
        recieve_cap_ls_reply(bot, trigger)
    # Server denied CAP REQ
    elif trigger.args[1] == 'NAK':
        entry = bot._cap_reqs.get(trigger, None)
        # If it was requested with bot.cap_req
        if entry:
            for req in entry:
                # And that request was mandatory/prohibit, and a callback was
                # provided
                if req[0] and req[2]:
                    # Call it.
                    req[2](bot, req[0] + trigger)
    # Server is acknowledinge SASL for us.
    elif (trigger.args[0] == bot.nick and trigger.args[1] == 'ACK' and
                  'sasl' in trigger.args[2]):
        recieve_cap_ack_sasl(bot)


def recieve_cap_ls_reply(bot, trigger):
    if bot.server_capabilities:
        # We've already seen the results, so someone sent CAP LS from a module.
        # We're too late to do SASL, and we don't want to send CAP END before
        # the module has done what it needs to, so just return
        return
    bot.server_capabilities = set(trigger.split(' '))

    # If some other module requests it, we don't need to add another request.
    # If some other module prohibits it, we shouldn't request it.
    if 'multi-prefix' not in bot._cap_reqs:
        # Whether or not the server supports multi-prefix doesn't change how we
        # parse it, so we don't need to worry if it fails.
        bot._cap_reqs['multi-prefix'] = (['', 'coretasks', None],)

    for cap, reqs in iteritems(bot._cap_reqs):
        # At this point, we know mandatory and prohibited don't co-exist, but
        # we need to call back for optionals if they're also prohibited
        prefix = ''
        for entry in reqs:
            if prefix == '-' and entry[0] != '-':
                entry[2](bot, entry[0] + cap)
                continue
            if entry[0]:
                prefix = entry[0]

        # It's not required, or it's supported, so we can request it
        if prefix != '=' or cap in bot.server_capabilities:
            # REQs fail as a whole, so we send them one capability at a time
            bot.write(('CAP', 'REQ', entry[0] + cap))
        elif reqs[2]:
            # Server is going to fail on it, so we call the failure function
            reqs[2](bot, entry[0] + cap)

    # If we want to do SASL, we have to wait before we can send CAP END. So if
    # we are, wait on 903 (SASL successful) to send it.
    if bot.config.core.sasl_password:
        bot.write(('CAP', 'REQ', 'sasl'))
    else:
        bot.write(('CAP', 'END'))


def recieve_cap_ack_sasl(bot):
    # Presumably we're only here if we said we actually *want* sasl, but still
    # check anyway.
    if not bot.config.core.sasl_password:
        return
    mech = bot.config.core.sasl_mechanism or 'PLAIN'
    bot.write(('AUTHENTICATE', mech))


@lpbot.module.event('AUTHENTICATE')
@lpbot.module.rule('.*')
def auth_proceed(bot, trigger):
    if trigger.args[0] != '+':
        # How did we get here? I am not good with computer.
        return
    # Is this right?
    if bot.config.core.sasl_username:
        sasl_username = bot.config.core.sasl_username
    else:
        sasl_username = bot.nick
    sasl_token = '\0'.join((sasl_username, sasl_username,
                            bot.config.core.sasl_password))
    # Spec says we do a base 64 encode on the SASL stuff
    bot.write(('AUTHENTICATE', base64.b64encode(sasl_token)))


@lpbot.module.event('903')
@lpbot.module.rule('.*')
def sasl_success(bot, trigger):
    bot.write(('CAP', 'END'))