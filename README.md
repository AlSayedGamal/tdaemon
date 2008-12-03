## Test Daemon

The test daemon watches the content of files in a directory and if any of them
changes (the content is edited), it runs the tests.

### Installation

Put the tdaemon somewhere where it's executable.

You may run like this:

    $ tdaemon.py --test-program=nose /path/to/python/project

The daemon starts watching the directory and subdirectories. As soon as one file
changes, the daemon runs the nosetests and you may watch the result.

Three test programs are available:

* nosetests (keyword is `nose` or `nosetests`)
* django (keyword is `django`)
* py.test (keyword is `py`)

When you're using django, the path to the project must be the path where
`manage.py` lives.

### TODO

    [ ] Erase the custom command option. Too dangerous
    [ ] Add an "custom argument" option. The user may want to run specific
        commands, but the only way to do so is to send arguments rather than the
        whole external command. Tests must pass, though (no `&`, for example)
    [ ] Extend the test utilities to other languages
    [ ] Add an "ignore" option to ignore other files (logs, sqlite database,
        image files, etc)

### Done

    [X] implements py.test, if possible
    [X] Fixing bug: when a file vanished, the program fails.
    [X] I remember I made the first bits of the code after reading an article...
        [X] Find the link and name of the original author
        [X] add appropriate credits
    [X] Bugfix: When doing (e.g.) hg commit, it opens temporary files that are
        detected as "changed", and the daemon starts tests. It should be ignored
        (ref. ignore-directories)
    [X] Feature: If the scanned directory size if larger than the option limit,
    asking for the user to accept processing or not. Default option limit is 25MB
    [X] Add the possibility to run a custom command.
        (eg. ``python manage.py test myapp.MyTest``)

