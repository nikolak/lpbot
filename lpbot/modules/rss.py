# -*- coding: utf-8 -*-

# Copyright 2012, Michael Yanovich, yanovich.net
# Copyright 2014, Nikola Kovacevic <nikolak@outlook.com>
# Copyright 2016, Benjamin Esser <benjamin.esser1@gmail.com>
# Licensed under the Eiffel Forum License 2.


from datetime import datetime
import time
import re
import socket
import feedparser

from lpbot.formatting import color, bold
from lpbot.module import commands, interval
from lpbot.config import ConfigurationError
from lpbot.logger import get_logger

LOGGER = get_logger(__name__)

socket.setdefaulttimeout(10)

INTERVAL = 60  # seconds between checking for new updates

# TODO: the original idea was to abstract all database interaction away from single modules
# and gather them in lpbot/db.py. This module is an exception because it uses its own db table
# and other modules are unlikely to reuse something like lpbot.db.set_rss_value(), but it
# would be nice to have for consistency reasons. Also, all this raw SQL is making the code
# harder to read than it needs to be, while db.py is already full of it (that's the point).

def setup(bot):
    #this is probably for reloading purposes (check modules/reload.py)
    bot.memory['rss_manager'] = RSSManager(bot)


@commands('rss')
def manage_rss(bot, trigger):
    """Manage RSS feeds. For a list of commands, type: .rss help"""
    bot.memory['rss_manager'].manage_rss(bot, trigger)


class RSSManager:
    def __init__(self, bot):
        self.running = True

        # get a list of all methods in this class that start with _rss_
        self.actions = sorted(method[5:] for method in dir(self) if method.startswith('_rss_'))

    def _show_doc(self, bot, command):
        """Given an RSS command, say the docstring for the corresponding method."""
        for line in getattr(self, '_rss_' + command).__doc__.split('\n'):
            line = line.strip()
            if line:
                bot.reply(line)

    def manage_rss(self, bot, trigger):
        """Manage RSS feeds. Usage: .rss <command>"""
        if not trigger.admin:
            bot.reply("Sorry, you need to be an admin to modify the RSS feeds.")
            return

        text = trigger.group().split()
        if (len(text) < 2 or text[1] not in self.actions):
            bot.reply("Usage: .rss <command>")
            bot.reply("Available RSS commands: " + ', '.join(self.actions))
            return

        # run the function
        getattr(self, '_rss_' + text[1])(bot, trigger)
        return


    def _rss_start(self, bot, trigger):
        """Start fetching feeds. Usage: .rss start"""
        bot.reply("Okay, I'll start fetching RSS feeds..." if not self.running else
                  "Continuing to fetch RSS feeds.")
        LOGGER.debug("RSS started.")
        self.running = True

    def _rss_stop(self, bot, trigger):
        """Stop fetching feeds. Usage: .rss stop"""
        bot.reply("Okay, I'll stop fetching RSS feeds..." if self.running else
                  "Not currently fetching RSS feeds.")
        LOGGER.debug("RSS stopped.")
        self.running = False

    def _rss_add(self, bot, trigger):
        """Add a feed to a channel, or modify an existing one.
        Set mIRC-style foreground and background colour indices using fg and bg.
        Usage: .rss add <#channel> <Feed_Name> <URL> [fg] [bg]
        """
        pattern = r'''
            ^\.rss\s+add
            \s+([~&#+!][^\s,]+)  # channel
            \s+("[^"]+"|[\w-]+)  # name, which can contain anything but quotes if quoted
            \s+(\S+)             # url
            (?:\s+(\d+))?        # foreground colour (optional)
            (?:\s+(\d+))?        # background colour (optional)
            '''
        match = re.match(pattern, trigger.group(), re.IGNORECASE | re.VERBOSE)
        if match is None:
            self._show_doc(bot, 'add')
            return

        channel = match.group(1)
        feed_name = match.group(2).strip('"')
        feed_url = match.group(3)
        fg = int(match.group(4)) % 16 if match.group(4) else None
        bg = int(match.group(5)) % 16 if match.group(5) else None

        result = bot.db._execute(
                      '''SELECT * FROM rss_feeds WHERE channel = ? AND feed_name = ?
                      ''',(channel, feed_name))
        if not result.fetchone():
            bot.db._execute('''
                INSERT INTO rss_feeds (channel, feed_name, feed_url, fg, bg)
                VALUES (?, ?, ?, ?, ?)
                ''', (channel, feed_name, feed_url, fg, bg))
            bot.reply("Successfully added the feed to the channel.")
        else:
            bot.db._execute('''
                UPDATE rss_feeds SET feed_url = ?, fg = ?, bg = ?
                WHERE channel = ? AND feed_name = ?
                ''', (feed_url, fg, bg, channel, feed_name))
            bot.reply("Successfully modified the feed.")
        return True

    def _rss_del(self, bot, trigger):
        """Remove one or all feeds from one or all channels.
        Usage: .rss del [#channel] [Feed_Name]
        """
        pattern = r"""
            ^\.rss\s+del
            (?:\s+([~&#+!][^\s,]+))?  # channel (optional)
            (?:\s+("[^"]+"|[\w-]+))? # name (optional)
            """
        match = re.match(pattern, trigger.group(), re.IGNORECASE | re.VERBOSE)
        # at least one of channel or feed name is required
        if match is None or (not match.group(1) and not match.group(2)):
            self._show_doc(bot, 'del')
            return

        channel = match.group(1)
        feed_name = match.group(2).strip('"') if match.group(2) else None
        args = [arg for arg in (channel, feed_name) if arg]

        result = bot.db._execute(('''
		             DELETE FROM rss_feeds WHERE '''
                     + ('channel = ? AND ' if channel else '')
                     + ('feed_name = ?' if feed_name else '')
                     ).rstrip(' AND '), args)

        if result.rowcount:
            noun = 'feeds' if result.rowcount != 1 else 'feed'
            bot.reply("Successfully removed {0} {1}.".format(result.rowcount, noun))
        else:
            bot.reply("No feeds matched the command.")

        return True

    def _rss_enable(self, bot, trigger):
        """Enable a feed or feeds. Usage: .rss enable [#channel] [Feed_Name]"""
        return self._toggle(bot, trigger)

    def _rss_disable(self, bot, trigger):
        """Disable a feed or feeds. Usage: .rss disable [#channel] [Feed_Name]"""
        return self._toggle(bot, trigger)

    def _toggle(self, bot, trigger):
        """Enable or disable a feed or feeds. Usage: .rss <enable|disable> [#channel] [Feed_Name]"""
        command = trigger.group(3)

        pattern = r"""
            ^\.rss\s+(enable|disable) # command
            (?:\s+([~&#+!][^\s,]+))?  # channel (optional)
            (?:\s+("[^"]+"|[\w-]+))?  # name (optional)
            """
        match = re.match(pattern, trigger.group(), re.IGNORECASE | re.VERBOSE)
        # at least one of channel or feed name is required
        if match is None or (not match.group(2) and not match.group(3)):
            self._show_doc(bot, command)
            return

        enabled = 1 if command == 'enable' else 0
        channel = match.group(2)
        feed_name = match.group(3).strip('"') if match.group(3) else None
        args = [arg for arg in (enabled, channel, feed_name) if arg is not None]

        result = bot.db._execute(('''
                     UPDATE rss_feeds SET enabled = ? WHERE '''
                     + ('channel = ? AND ' if channel else '')
                     + ('feed_name = ?' if feed_name else '')
                     ).rstrip(' AND '), args)

        if result.rowcount:
            noun = 'feeds' if result.rowcount != 1 else 'feed'
            bot.reply("Successfully {0}d {1} {2}.".format(command, result.rowcount, noun))
        else:
            bot.reply("No feeds matched the command.")

        return True

    def _rss_list(self, bot, trigger):
        """Get information on all feeds in the database. Usage: .rss list [#channel] [Feed_Name]"""
        pattern = r"""
            ^\.rss\s+list
            (?:\s+([~&#+!][^\s,]+))?  # channel (optional)
            (?:\s+("[^"]+"|[\w-]+))? # name (optional)
            """
        match = re.match(pattern, trigger.group(), re.IGNORECASE | re.VERBOSE)
        if match is None:
            self._show_doc(bot, 'list')
            return

        channel = match.group(1)
        feed_name = match.group(2).strip('"') if match.group(2) else None

        feeds = [RSSFeed(row) for row in 
                 bot.db._execute('SELECT * FROM rss_feeds').fetchall()]

        if not feeds:
            bot.reply("No RSS feeds in the database.")
            return

        filtered = [feed for feed in feeds
                    if (feed.channel == channel or channel is None)
                    and (feed_name is None or feed.name.lower() == feed_name.lower())]

        if not filtered:
            bot.reply("No feeds matched the command.")
            return

        noun = 'feeds' if len(feeds) != 1 else 'feed'
        bot.reply("Showing {0} of {1} RSS {2} in the database:".format(
            len(filtered), len(feeds), noun))

        for feed in filtered:
            bot.say("  {0} {1} {2}{3} {4} {5}".format(
                    feed.channel,
                    color(feed.name, feed.fg, feed.bg),
                    feed.url,
                    " (disabled)" if not feed.enabled else '',
                    feed.fg, feed.bg))

    def _rss_fetch(self, bot, trigger):
        """Force all RSS feeds to be fetched immediately. Usage: .rss fetch"""
        read_feeds(bot, True)

    def _rss_help(self, bot, trigger):
        """Get help on any of the RSS feed commands. Usage: .rss help <command>"""
        command = trigger.group(4)
        if command in self.actions:
            self._show_doc(bot, command)
        else:
            bot.reply("For help on a command, type: .rss help <command>")
            bot.reply("Available RSS commands: " + ', '.join(self.actions))


class RSSFeed:
    """Represent a single row in the feed table."""

    def __init__(self, row):
        """Initialize with values from the feed table."""
        columns = ('channel',
                   'name',
                   'url',
                   'fg',
                   'bg',
                   'enabled',
                   'title',
                   'link',
                   'published',
                   'etag',
                   'modified',
                   )
        for i, column in enumerate(columns):
            setattr(self, column, row[i])


def _disable_feed(feed):
    bot.db._execute('''
        UPDATE rss_feeds SET enabled = ?
        WHERE channel = ? AND feed_name = ?
        ''', (0, feed.channel, feed.name))


@interval(INTERVAL)
def read_feeds(bot, force=False):
    if not bot.memory['rss_manager'].running and not force:
        return

    feeds = bot.db._execute('SELECT * FROM rss_feeds').fetchall()
    if not feeds:
        return

    for feed_row in feeds:
        feed = RSSFeed(feed_row)
        if not feed.enabled:
            continue

        try:
            fp = feedparser.parse(feed.url, etag=feed.etag, modified=feed.modified)
        except IOError as e:
            LOGGER.exception("Can't parse feed on %s, disabling.",
                             feed.name)
            _disable_feed(feed)
            continue

        # fp.status will only exist if pulling from an online feed
		# fp.version sometimes runs into AttributeError
        fp.status = getattr(fp, 'status', 'unknown')
        fp.version = getattr(fp, 'version', 'unknown')
        
        LOGGER.debug("%s: status = %s, version = '%s', items = %s",
                     feed.name, fp.status, fp.version, len(fp.entries))
        # check HTTP status
        if status == 301:  # MOVED_PERMANENTLY
            bot.warning(
                "Got HTTP 301 (Moved Permanently) on %s, updating URI to %s",
                feed.name, fp.href
            )
            bot.db._execute('''
                UPDATE rss_feeds SET feed_url = ?
                WHERE channel = ? AND feed_name = ?
                ''', (fp.href, feed.channel, feed.name))

        elif status == 410:  # GONE
            LOGGER.warning("Got HTTP 410 (Gone) on {0}, disabling",
                           feed.name)
            _disable_feed(feed)

        if not fp.entries:
            continue

        feed_etag = getattr(fp, 'etag', None)
        feed_modified = getattr(fp, 'modified', None)

        entry = fp.entries[0]
        # parse published and updated times into datetime objects (or None)
        entry_dt = (datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    if hasattr(entry, 'published_parsed') else None)
        entry_update_dt = (datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                           if hasattr(entry, 'updated_parsed') else None)

        # check if article is new, and skip otherwise
        if (feed.title == entry.title and feed.link == entry.link
                and feed.etag == feed_etag and feed.modified == feed_modified):
            LOGGER.info(u"Skipping previously read entry: [%s] %s",
                        feed.name, entry.title)
            continue

        # save article title, url, and modified date
        bot.db._execute('''
            UPDATE rss_feeds
            SET article_title = ?, article_url = ?, published = ?, etag = ?, modified = ?
            WHERE channel = ? AND feed_name = ?
            ''', (entry.title, entry.link, entry_dt, feed_etag, feed_modified,
                  feed.channel, feed.name))

        if feed.published and entry_dt:
            published_dt = datetime.strptime(feed.published, "%Y-%m-%d %H:%M:%S")
            if published_dt >= entry_dt:
                # This will make more sense once iterating over the feed is
                # implemented. Once that happens, deleting or modifying the
                # latest item would result in the whole feed getting re-msg'd.
                # This will prevent that from happening.
                LOGGER.info(
                    "Skipping older entry: [%s] %s, because %s >= %s",
                    feed.name, entry.title, published_dt, entry_dt)
                continue

        # Don't use long reddit urls, use short version

        entry_link = entry.link
        if "www.reddit.com/r/" in entry.link:
            short_url = "https://redd.it/{}"
            reddit_re= "https://www\.reddit\.com\/r\/.*comments/(.*?)\/"
            try:
                entry_link = short_url.format(re.search(reddit_re, entry_link).group(1))
            except:
                LOGGER.debug("Matching reddit url {} failed".format(entry_link))

        # create message for new entry
        message = u"[{0}] {1} - {2}".format(
            bold(color(feed.name, feed.fg, feed.bg)), bold(entry.title), entry_link)

        # append update time if it exists, or published time if it doesn't
        # timestamp = entry_update_dt or entry_dt
        # if timestamp:
        #     # attempt to get time format from preferences
        #     tformat = bot.db.get_channel_value(feed.channel, 'time_format')
        #     if not tformat and bot.config.has_option('clock', 'time_format'):
        #         tformat = bot.config.clock.time_format
        #
        #     message += " - {0}".format(timestamp.strftime(tformat or '%F - %T%Z'))

        # print message
        bot.msg(feed.channel, message)
