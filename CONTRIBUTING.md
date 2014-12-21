Submitting Issues
-----------------

When submitting issues to our
[issue tracker](https://github.com/nikola-k/willie/issues), it's important
that you do the following:

1. Describe your issue clearly and concisely.
2. Give Willie the .version command, and include the output in your issue.
3. Note the OS you're running Willie on, and how you installed Willie (via your
package manager, pip, setup.py install, or running straight from source)
4. Include relevant output from the log files in ~/.willie/logs.

Committing Code
---------------
We prefer code to be submitted through GitHub pull requests.

In order to make it easier for us to review and merge your code, it's important
to write good commits, and good commit messages. Below are some things you
should do when you want to submit code. These aren't hard and fast rules; we
may still consider code that doesn't meet all of them. But doing the stuff
below will make our lives easier, and by extension make us more likely to
include your changes.

* Commits should focus on one thing at a time. Do include whatever you need to
  make your change work, but avoid putting unrelated changes in the same commit.
  Preferably, one change in functionality should be in exactly one commit.
* pep8ify your code before you commit.
* Test your code before you commit. We don't have a formal testing plan in
  place, but you should make sure your code works as promised before you commit.
* Make your commit messages clear and explicative. Our convention is to place
  the name of the thing you're changing in [brackets] at the beginning of the
  message: the module name for modules, [docs] for documentation files,
  [coretasks] for coretasks.py, [db] for the database feature, and so on.
* Python files should always have `#coding: utf8` as the first line (or the
  second, if the first is `#!/usr/bin/env python`), and
  `from __future__ import unicode_literals` as the first line after the module
  docstring.
