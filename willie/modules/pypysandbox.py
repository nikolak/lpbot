#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Popen, child process taken from
# http://stackoverflow.com/questions/1191374/subprocess-with-timeout
# PyPy code from: https://github.com/raylu/pbot/blob/master/commands.py

from __future__ import unicode_literals

import os
import subprocess
import time
import select
import errno

from willie.module import commands, example

PATH = os.environ['PATH']


class Popen(subprocess.Popen):
    def communicate(self, input=None, timeout=None):
        if timeout is None:
            return subprocess.Popen.communicate(self, input)

        if self.stdin:
            # Flush stdio buffer, this might block if user
            # has been writing to .stdin in an uncontrolled
            # fashion.
            self.stdin.flush()
            if not input:
                self.stdin.close()

        read_set, write_set = [], []
        stdout = stderr = None

        if self.stdin and input:
            write_set.append(self.stdin)
        if self.stdout:
            read_set.append(self.stdout)
            stdout = []
        if self.stderr:
            read_set.append(self.stderr)
            stderr = []

        input_offset = 0
        deadline = time.time() + timeout

        while read_set or write_set:
            try:
                rlist, wlist, xlist = select.select(read_set, write_set, [], max(0, deadline - time.time()))
            except select.error as ex:
                if ex.args[0] == errno.EINTR:
                    continue
                raise

            if not (rlist or wlist):
                # Just break if timeout
                # Since we do not close stdout/stderr/stdin, we can call
                # communicate() several times reading data by smaller pieces.
                break

            if self.stdin in wlist:
                chunk = input[input_offset:input_offset + subprocess._PIPE_BUF]
                try:
                    bytes_written = os.write(self.stdin.fileno(), chunk)
                except OSError as ex:
                    if ex.errno == errno.EPIPE:
                        self.stdin.close()
                        write_set.remove(self.stdin)
                    else:
                        raise
                else:
                    input_offset += bytes_written
                    if input_offset >= len(input):
                        self.stdin.close()
                        write_set.remove(self.stdin)

            # Read stdout / stderr by 1024 bytes
            for fn, tgt in (
                    (self.stdout, stdout),
                    (self.stderr, stderr),
            ):
                if fn in rlist:
                    data = os.read(fn.fileno(), 1024)
                    if data == '':
                        fn.close()
                        read_set.remove(fn)
                    tgt.append(data)

        if stdout is not None:
            stdout = ''.join(stdout)
        if stderr is not None:
            stderr = ''.join(stderr)

        return (self.pid, stdout, stderr)


def get_process_children(pid):
    p = Popen('ps --no-headers -o pid --ppid %d' % pid, shell=True,
              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return [int(p) for p in stdout.split()]


def python(code):
    pypy = Popen(['pypy-sandbox'],
                 stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE,
                 env={'PATH': PATH},
                 universal_newlines=True,
                 preexec_fn=os.setpgrp)

    start = time.time()
    pid, stdout, stderr = pypy.communicate(code, timeout=5)

    end = time.time()
    # os.system("killall pypy-c-sandbox")

    for process_pid in [pid] + get_process_children(pid):
        os.system("kill {}".format(process_pid))

    if end - start > 4:
        return "Timed out"

    errlines = stderr.split('\n')
    if len(errlines) > 3:
        for i in range(1, len(errlines)):
            line = errlines[-i]  # iterate backwards
            if line:
                return line[:250]
    else:
        for line in stdout.split('\n'):
            if line.startswith('>>>> '):
                while line[:5] in ['>>>> ', '.... ']:
                    line = line[5:]
                return line[:250]


@commands('python', 'py')
@example('.py len([1,2,3])')
def bing(bot, trigger):
    code = trigger.group(2)
    result = python(code)
    bot.say(result)