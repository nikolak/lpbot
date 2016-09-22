# -*- coding: utf-8 -*-

import json
import os.path
import sqlite3


def _deserialize(value):
    if value is None:
        return None
    # sqlite likes to return ints for strings that look like ints, even though
    # the column type is string. That's how you do dynamic typing wrong.
    value = str(value)
    # Just in case someone's mucking with the DB in a way we can't account for,
    # ignore json parsing errors
    try:
        value = json.loads(value)
    except:
        pass
    return value


class lpbotDB(object):

    def __init__(self, config):
        self.filename = config.core.db_filename
        if self.filename is None:
            self.filename = os.path.splitext(config.filename)[0] + '.db'
        self._create()


    def _execute(self, *args, **kwargs):
        """Execute an arbitrary SQL query against the database.

        Returns a cursor object, on which things like `.fetchall()` can be
        called per PEP 249."""
        with sqlite3.connect(self.filename) as conn:
            cur = conn.cursor()
            return cur.execute(*args, **kwargs)


    def _create(self):
        """Create the basic database structure."""
        self._execute(
            """CREATE TABLE IF NOT EXISTS `nickname` (
                `id`	INTEGER PRIMARY KEY AUTOINCREMENT,
                `name`	VARCHAR NOT NULL,
                `key`	VARCHAR NOT NULL,
                `value`	VARCHAR NOT NULL
            )"""
        )

        self._execute(
		    """CREATE TABLE IF NOT EXISTS rss_feeds (
               channel TEXT,
               feed_name TEXT,
               feed_url TEXT,
               fg TINYINT,
               bg TINYINT,
               enabled BOOL DEFAULT 1,
               article_title TEXT,
               article_url TEXT,
               published TEXT,
               etag TEXT,
               modified TEXT,
               PRIMARY KEY (channel, feed_name)
            )"""
		)

        self._execute(
            'CREATE TABLE IF NOT EXISTS `channel_values` '
            '(channel STRING, key STRING, value STRING, '
            'PRIMARY KEY (channel, key))'
        )


    def set_channel_value(self, channel, key, value):
        """Sets the value for a given key to be associated with the channel."""
        channel = channel.lower()
        value = json.dumps(value, ensure_ascii=False)
        self._execute('INSERT OR REPLACE INTO channel_values VALUES (?, ?, ?)',
                     [channel, key, value])


    def get_channel_value(self, channel, key):
        """Retrieves the value for a given key associated with a channel."""
        channel = channel.lower()
        result = self._execute(
            'SELECT value FROM channel_values WHERE channel = ? AND key = ?',
            [channel, key]
        ).fetchone()
        if result is not None:
            result = result[0]
        return _deserialize(result)

    def get_url(self):
        """Returns a URL for the database, usable to connect with SQLAlchemy.
        """
        return 'sqlite://{}'.format(self.filename)


    def set_nick_value(self, nick, key, value):
        """Sets the value for a given key to be associated with the nick."""
        nick_id = None

        try:
            row = self._execute('SELECT id FROM nickname WHERE name = ? AND key = ?',[nick.lower(), key]).fetchone()
            nick_id = row[0]
        except:
            pass
        value = json.dumps(value, ensure_ascii=False)
        self._execute('INSERT OR REPLACE INTO nickname VALUES (?, ?, ?, ?)',
                     [nick_id, nick.lower(), key, value])


    def get_nick_value(self, nick, key):
        """Retrieves the value for a given key associated with a nick."""
        result = self._execute(
            'SELECT value FROM nickname WHERE name = ? AND key = ?',
            [nick.lower(), key]).fetchone()
        if result is not None:
            result = result[0]
        return _deserialize(result)
