#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# Original code copyright:
# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright © 2012-2014, Elad Alfassa <elad@fedoraproject.org>
# Licensed under the Eiffel Forum License 2.

from __future__ import unicode_literals
from __future__ import print_function

import sys

from lpbot.tools import stderr


if sys.version_info.major < 3:
    stderr('Requires python 3')
    sys.exit(1)

import os
import argparse
import signal

from lpbot.__init__ import run, __version__
from lpbot.config import Config, create_config, ConfigurationError, wizard
import lpbot.tools as tools

homedir = os.path.join(os.path.expanduser('~'), '.lpbot')


def enumerate_configs(extension='.cfg'):
    configfiles = []
    if os.path.isdir(homedir):
        willie_dotdirfiles = os.listdir(homedir)  # Preferred
        for item in willie_dotdirfiles:
            if item.endswith(extension):
                configfiles.append(item)

    return configfiles


def find_config(name, extension='.cfg'):
    if os.path.isfile(name):
        return name
    configs = enumerate_configs(extension)
    if name in configs or name + extension in configs:
        if name + extension in configs:
            name = name + extension

    return os.path.join(homedir, name)


def main(argv=None):
    global homedir
    # Step One: Parse The Command Line
    try:
        parser = argparse.ArgumentParser(description='lpbot IRC Bot',
                                         usage='%(prog)s [options]')
        parser.add_argument('-c', '--config', metavar='filename',
                            help='use a specific configuration file')
        parser.add_argument("-d", '--fork', action="store_true",
                            dest="deamonize", help="Deamonize lpbot")
        parser.add_argument("-q", '--quit', action="store_true", dest="quit",
                            help="Gracefully quit lpbot")
        parser.add_argument("-k", '--kill', action="store_true", dest="kill",
                            help="Kill lpbot")
        parser.add_argument('--exit-on-error', action="store_true",
                            dest="exit_on_error", help=(
                "Exit immediately on every error instead of "
                "trying to recover"))
        parser.add_argument("-l", '--list', action="store_true",
                            dest="list_configs",
                            help="List all config files found")
        parser.add_argument("-m", '--migrate', action="store_true",
                            dest="migrate_configs",
                            help="Migrate config files to the new format")
        parser.add_argument('--quiet', action="store_true", dest="quiet",
                            help="Supress all output")
        parser.add_argument('-w', '--configure-all', action='store_true',
                            dest='wizard', help='Run the configuration wizard.')
        parser.add_argument('--configure-modules', action='store_true',
                            dest='mod_wizard', help=(
                'Run the configuration wizard, but only for the '
                'module configuration options.'))
        parser.add_argument('--configure-database', action='store_true',
                            dest='db_wizard', help=(
                'Run the configuration wizard, but only for the '
                'database configuration options.'))
        parser.add_argument('-v', '--version', action="store_true",
                            dest="version", help="Show version number and exit")
        opts = parser.parse_args()

        try:
            if os.getuid() == 0 or os.geteuid() == 0:
                stderr("Don't runt he bot as root")
                sys.exit(1)
        except AttributeError:
            # Windows doesn't have os.getuid/os.geteuid
            pass

        if opts.version:
            py_ver = '%s.%s.%s' % (sys.version_info.major,
                                   sys.version_info.minor,
                                   sys.version_info.micro)
            print('lpbot %s (running on python %s)' % (__version__, py_ver))
            return
        elif opts.wizard:
            wizard('all', opts.config)
            return
        elif opts.mod_wizard:
            wizard('mod', opts.config)
            return
        elif opts.db_wizard:
            wizard('db', opts.config)
            return

        if opts.list_configs:
            configs = enumerate_configs()
            print('Config files in ~/.lpbot:')
            if len(configs) is 0:
                print('\tNone found')
            else:
                for config in configs:
                    print('\t%s' % config)
            print('-------------------------')
            return

        config_name = opts.config or 'default'

        configpath = find_config(config_name)
        if not os.path.isfile(configpath):
            print("Welcome to lpbot!\nI can't seem to find the configuration file, so let's generate it!\n")
            if not configpath.endswith('.cfg'):
                configpath = configpath + '.cfg'
            create_config(configpath)
            configpath = find_config(config_name)
        try:
            config_module = Config(configpath)
        except ConfigurationError as e:
            stderr(e)
            sys.exit(2)

        if config_module.core.not_configured:
            stderr('Bot is not configured, can\'t start')
            # exit with code 2 to prevent auto restart on fail by systemd
            sys.exit(2)

        if not config_module.has_option('core', 'homedir'):
            config_module.dotdir = homedir
            config_module.homedir = homedir
        else:
            homedir = config_module.core.homedir
            config_module.dotdir = config_module.core.homedir

        if not config_module.core.logdir:
            config_module.core.logdir = os.path.join(homedir, 'logs')
        logfile = os.path.os.path.join(config_module.logdir, 'stdio.log')
        if not os.path.isdir(config_module.logdir):
            os.mkdir(config_module.logdir)

        config_module.exit_on_error = opts.exit_on_error
        config_module._is_deamonized = opts.deamonize

        sys.stderr = tools.OutputRedirect(logfile, True, opts.quiet)
        sys.stdout = tools.OutputRedirect(logfile, False, opts.quiet)

        # Handle --quit, --kill and saving the PID to file
        pid_dir = config_module.core.pid_dir or homedir
        if opts.config is None:
            pid_file_path = os.path.join(pid_dir, 'lpbot.pid')
        else:
            basename = os.path.basename(opts.config)
            if basename.endswith('.cfg'):
                basename = basename[:-4]
            pid_file_path = os.path.join(pid_dir, 'lpbot-%s.pid' % basename)
        if os.path.isfile(pid_file_path):
            with open(pid_file_path, 'r') as pid_file:
                try:
                    old_pid = int(pid_file.read())
                except ValueError:
                    old_pid = None
            if old_pid is not None and tools.check_pid(old_pid):
                if not opts.quit and not opts.kill:
                    stderr('There\'s already a lpbot instance running with this config file')
                    stderr('Try using the --quit or the --kill options')
                    sys.exit(1)
                elif opts.kill:
                    stderr('Killing the lpbot')
                    os.kill(old_pid, signal.SIGKILL)
                    sys.exit(0)
                elif opts.quit:
                    stderr('Signaling lpbot to stop gracefully')
                    if hasattr(signal, 'SIGUSR1'):
                        os.kill(old_pid, signal.SIGUSR1)
                    else:
                        os.kill(old_pid, signal.SIGTERM)
                    sys.exit(0)
            elif not tools.check_pid(old_pid) and (opts.kill or opts.quit):
                stderr('lpbot is not running!')
                sys.exit(1)
        elif opts.quit or opts.kill:
            stderr('lpbot is not running!')
            sys.exit(1)
        if opts.deamonize:
            child_pid = os.fork()
            if child_pid is not 0:
                sys.exit()
        with open(pid_file_path, 'w') as pid_file:
            pid_file.write(str(os.getpid()))
        config_module.pid_file_path = pid_file_path

        # Step Five: Initialise And Run lpbot
        run(config_module)
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        os._exit(1)


if __name__ == '__main__':
    main()
