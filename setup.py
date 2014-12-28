#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from distutils.core import setup
import tempfile
import sys
import os
import shutil

from lpbot import __version__


requires = ['feedparser', 'pytz', 'lxml', 'praw', 'enchant', 'pygeoip']
if sys.version_info.major < 3:
    requires.append('backports.ssl_match_hostname')


def do_setup():
    try:
        # This special screwing is to make willie.py get installed to PATH as
        # willie, not willie.py. Don't remove it, or you'll break it.
        tmp_dir = tempfile.mkdtemp()
        tmp_main_script = os.path.join(tmp_dir, 'lpbot')
        shutil.copy('lpbot.py', tmp_main_script)

        setup(
            name='lpbot',
            version=__version__,
            description='IRC bot based on willie bot',
            author='Nikola Kovacevic',
            author_email='nikolak@outlook.com',
            url='https://github.com/Nikola-K/lpbot',
            long_description="""lpbot is an IRC bot based on open source willie bot by Edward POWELL""",
            # Distutils is shit, and doesn't check if it's a list of basestring
            # but instead requires str.
            packages=[str('lpbot'), str('lpbot.modules')],
            scripts=[tmp_main_script],
            license='Eiffel Forum License, version 2',
            platforms='Linux x86, x86-64',
            requires=requires
        )
    finally:
        try:
            shutil.rmtree(tmp_dir)
        except OSError as e:
            if e.errno != 2:  # The directory is already gone, so ignore it
                raise


if __name__ == "__main__":
    do_setup()
