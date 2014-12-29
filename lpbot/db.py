# -*- coding: utf-8 -*-

import json
import os.path
import sqlite3


def _deserialize(value):
    if value is None:
        return None
    # sqlite likes to return ints for strings that look like ints, even though
    # the column type is string. That's how you do dynamic typing wrong.
    value = unicode(value)
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

    def connect(self):
        """Return a raw database connection object."""
        return sqlite3.connect(self.filename)

    def execute(self, *args, **kwargs):
        """Execute an arbitrary SQL query against the database.

        Returns a cursor object, on which things like `.fetchall()` can be
        called per PEP 249."""
        with self.connect() as conn:
            cur = conn.cursor()
            return cur.execute(*args, **kwargs)

    def _create(self):
        """Create the basic database structure."""
        # Do nothing if the db already exists.
        try:
            self.execute('SELECT * FROM nickname;')
            self.execute('SELECT * FROM rssfeed;')
        except:
            pass
        else:
            return

        self.execute(
            """CREATE TABLE `nickname` (
                `id`	INTEGER PRIMARY KEY AUTOINCREMENT,
                `name`	VARCHAR NOT NULL,
                `key`	VARCHAR NOT NULL,
                `value`	VARCHAR NOT NULL
            )"""
        )

        self.execute(
            """CREATE TABLE `rssfeed` (
                `id`	INTEGER PRIMARY KEY AUTOINCREMENT,
                `name`	TEXT,
                `url`	TEXT NOT NULL,
                `channel`	TEXT,
                `enabled`	INTEGER DEFAULT 1,
                `last_link`	TEXT,
                `last_pubdate`	TEXT
            )"""
        )

    def get_url(self):
        """Returns a URL for the database, usable to connect with SQLAlchemy.
        """
        return 'sqlite://{}'.format(self.filename)


    def set_nick_value(self, nick, key, value):
        """Sets the value for a given key to be associated with the nick."""
        value = json.dumps(value, ensure_ascii=False)
        self.execute('INSERT OR REPLACE INTO nickname VALUES (?, ?, ?, ?)',
                     [None, nick, key, value])

    def get_nick_value(self, nick, key):
        """Retrieves the value for a given key associated with a nick."""
        result = self.execute(
            'SELECT value FROM nickname WHERE name = ? AND key = ?',
            [nick.lower(), key]
        ).fetchone()
        if result is not None:
            result = result[0]
        return _deserialize(result)
