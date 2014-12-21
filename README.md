Introduction
------------

Fork of willie bot primarily intended for /r/learnpython IRC channel use.

You should probably use the original repo if you want to run non-/r/learnpython
specific instance  yourself. Even though this fork does not contain any major backend changes and will probably
work on all channels and servers just like original version, such changes may be introduced
in the future.

Modules, and all other changes, are written with **only** python 2 support in mind.

**New modules and files should be licensed under Apache License 2.0, see APACHE LICENSE for more info**

Original files and changes to them are licensed under "Eiffel Forum License, version 2", 
see bottom of this readme or COPYING for license text.

For pypy sandbox feature to work you need to install pypy-sandbox, it's usually available in repos
and can be installed by typing `apt-get install python-pypy.sandbox`.

TODO
----

* Remove willie references and usages

* Write module writing tutorial and some docs

* Remove unnecessary modules

* Go through modules and fix the broken ones - a lot of them are broken

* Code refactoring, PEP8 and other changes are necessary

* Improve code docs

* Use SQLAlchemy as db (maybe)

* Improve logging - e.g. the logs now contain random newlline characters due to dumping raw text into file


Installation
------------

First, either clone the repository with `git clone
git://github.com/nikola-k/willie.git` or download a tarball from GitHub.

Willie requirements can be installed by running `pip install -r requirements.txt`.

If you have trouble installing `lxml` you can find it in your distro repos or download
binary build for windows from various websites.


In the source directory (whether cloned or from the tarball) run
`setup.py install`. You can then run `willie` to configure and start the
bot. Alternately, you can just run the `willie.py` file in the source
directory.

Adding modules
--------------
The easiest place to put new modules is in `~/.willie/modules`. You will need
to add a a line to the `[core]` section of your config file saying
`extra = /home/yourname/.willie/modules`.


TODO

Further documentation
---------------------

TODO

Other
-----

For a list of contributions to the Jenni fork see the file `CREDITS`.


Original License
----------------

     Eiffel Forum License, version 2

      1. Permission is hereby granted to use, copy, modify and/or
         distribute this package, provided that:
             * copyright notices are retained unchanged,
             * any distribution of this package, whether modified or not,
         includes this license text.
      2. Permission is hereby also granted to distribute binary programs
         which depend on this package. If the binary program depends on a
         modified version of this package, you are encouraged to publicly
         release the modified version of this package.

      ***********************

       THIS PACKAGE IS PROVIDED "AS IS" AND WITHOUT WARRANTY. ANY EXPRESS OR
       IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
       WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
       DISCLAIMED. IN NO EVENT SHALL THE AUTHORS BE LIABLE TO ANY PARTY FOR ANY
       DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
       DAMAGES ARISING IN ANY WAY OUT OF THE USE OF THIS PACKAGE.
    
       ***********************
