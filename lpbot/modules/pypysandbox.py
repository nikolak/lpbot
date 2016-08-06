# #!/usr/bin/env python
# # -*- coding: utf-8 -*-

# # PyPy code from: https://github.com/raylu/pbot/blob/master/commands.py



# import os
# from subprocess import Popen, PIPE, TimeoutExpired
# import signal

# from lpbot.module import commands, example


# PATH = os.environ['PATH']


# def get_process_children(pid):
#     p = Popen('ps --no-headers -o pid --ppid %d' % pid, shell=True,
#               stdout=PIPE, stderr=PIPE)
#     stdout, stderr = p.communicate()
#     return [int(p) for p in stdout.split()]


# def python(code):
#     pypy = Popen(['pypy-sandbox'],
#                  stdin=PIPE, stdout=PIPE,
#                  stderr=PIPE,
#                  env={'PATH': PATH},
#                  universal_newlines=True,
#                  preexec_fn=os.setpgrp)
#     try:
#         stdout, stderr = pypy.communicate(code, timeout=5)
#     except TimeoutExpired:
#         os.killpg(pypy.pid, signal.SIGKILL)
#         return "Timed out..."

#     errlines = stderr.split('\n')
#     if len(errlines) > 3:
#         for i in range(1, len(errlines)):
#             line = errlines[-i]  # iterate backwards
#             if line:
#                 return line[:250]
#     else:
#         for line in stdout.split('\n'):
#             if line.startswith('>>>> '):
#                 while line[:5] in ['>>>> ', '.... ']:
#                     line = line[5:]
#                 return line[:250]


# @commands('python', 'py')
# @example('.py len([1,2,3])')
# def bing(bot, trigger):
#     pass
#     code = trigger.group(2)
#     result = python(code)
#     bot.say(result)
