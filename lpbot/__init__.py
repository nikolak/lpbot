# -*- coding: utf-8 -*-

# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright 2012, Edward Powell, http://embolalia.net
# Copyright © 2012, Elad Alfassa <elad@fedoraproject.org>
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals
from __future__ import absolute_import

import os
import time
import traceback
import signal

__version__ = '2.1.0-beta'


def run(config):
    import lpbot.bot as bot
    # import lpbot.web as web
    import lpbot.logger
    from lpbot.tools import stderr

    if config.core.delay is not None:
        delay = config.core.delay
    else:
        delay = 20

    def signal_handler(sig, frame):
        if sig == signal.SIGUSR1 or sig == signal.SIGTERM:
            stderr('Got quit signal, shutting down.')
            p.quit('Closing')

    while True:
        try:
            p = bot.LpBot(config)
            if hasattr(signal, 'SIGUSR1'):
                signal.signal(signal.SIGUSR1, signal_handler)
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, signal_handler)
            lpbot.logger.setup_logging(p)
            p.run(config.core.host, int(config.core.port))
        except KeyboardInterrupt:
            break
        except Exception as e:
            trace = traceback.format_exc()
            try:
                stderr(trace)
            except:
                pass
            logfile = open(os.path.join(config.logdir, 'exceptions.log'), 'a')
            logfile.write('Critical exception in core')
            logfile.write(trace)
            logfile.write('----------------------------------------\n\n')
            logfile.close()
            os.unlink(config.pid_file_path)
            os._exit(1)

        if not isinstance(delay, int):
            break
        if p.hasquit or config.exit_on_error:
            break
        stderr('Warning: Disconnected. Reconnecting in %s seconds...' % delay)
        time.sleep(delay)
    os.unlink(config.pid_file_path)
    os._exit(0)
