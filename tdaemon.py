#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
Multi-engine Test Daemon in Python

Original concept by Jeff Winkler in:
http://jeffwinkler.net/nosy-run-python-unit-tests-automatically/

The present code is published under the terms of the MIT License. See LICENSE
file for more details.
"""

import sys
import os
from stat import *
import optparse
from time import sleep
import hashlib
import commands
import datetime
import re

IGNORE_EXTENSIONS = ('pyc', 'pyo')
IGNORE_DIRS = ('.bzr', '.git', '.hg', '.darcs', '.svn')
IMPLEMENTED_TEST_PROGRAMS = ('nose', 'nosetests', 'django', 'py')

# -------- Exceptions
class InvalidTestProgram(Exception):
    pass

class InvalidFilePath(Exception):
    pass

class Watcher(object):
    """
    Watcher class. This is the daemon that is watching every file in the
    directory and subdirectories, and that runs the test process.
    """
    file_list = {}
    debug = False
    use_custom_command = False

    def __init__(self, file_path, test_program, debug=False, custom_command=None):
        # check configuration
        self.check_configuration(file_path, test_program, custom_command)
        self.file_path = file_path
        self.file_list = self.walk(file_path)
        if not custom_command:
            self.test_program = test_program
        else:
            self.test_program = custom_command
            self.use_custom_command = True

        self.debug = debug

    def check_configuration(self, file_path, test_program, custom_command):
        """Checks if configuration is ok."""
        # checking filepath
        if not os.path.isdir(file_path):
            raise InvalidFilePath("""INVALID CONFIGURATION: file path %s is not a directory""" %
                os.path.abspath(file_path)
            )

        # checking test_program option
        if not custom_command and test_program not in IMPLEMENTED_TEST_PROGRAMS:
            raise InvalidTestProgram("""INVALID CONFIGURATION: The test program %s is unknown. Valid options are %s"""  % (test_program,  ', '.join(IMPLEMENTED_TEST_PROGRAMS)))

    def include(self, path):
        """Returns `True` if the file is not ignored"""
        for extension in IGNORE_EXTENSIONS:
            if path.endswith(extension):
                return False
        parts = path.split(os.path.sep)
        for part in parts:
            if part in IGNORE_DIRS:
                return False
        return True

    def walk(self, top, file_list={}):
        """Walks the walk. nah, seriously: reads the file and stores a hashkey
        corresponding to its content."""
        for root, dirs, files in os.walk(top, topdown=False):
            if os.path.basename(root) in IGNORE_DIRS:
                # Do not dig in ignored dirs
                continue

            for name in files:
                full_path = os.path.join(root, name)
                if self.include(full_path):
                    if os.path.isfile(full_path):
                        # preventing fail if the file vanishes
                        content = open(full_path).read()
                        file_list[full_path] = hashlib.sha224(content).hexdigest()
            for name in dirs:
                if name not in IGNORE_DIRS:
                    self.walk(os.path.join(root, name), file_list)
        return file_list

    def file_sizes(self):
        size = sum(map(os.path.getsize, self.file_list))
        return size / 1024 / 1024


    def diff_list(self, list1, list2):
        """Extracts differences between lists. For debug purposes"""
        for key in list1:
            if key in list2 and list2[key] != list1[key]:
                print key
            elif key not in list2:
                print key

    def run(self, cmd):
        """Runs the appropriate command"""
        print datetime.datetime.now()
        output = commands.getoutput(cmd)
        print output

    def run_tests(self):
        """Execute tests"""
        cmd = None
        if self.use_custom_command:
            cmd = self.test_program
        elif self.test_program in ('nose', 'nosetests'):
            cmd = "cd %s && nosetests" % self.file_path
        elif self.test_program == 'django':
            cmd = "python %s/manage.py test" % self.file_path
        elif self.test_program == 'py':
            cmd = 'py.test %s' % self.file_path

        if not cmd:
            raise InvalidTestProgram("The test program %s is unknown."
                "Valid options are `nose` and `django`" % self.test_program)

        self.run(cmd)

    def loop(self):
        """Main loop daemon."""
        while True:
            sleep(1)
            new_file_list = self.walk(self.file_path, {})
            if new_file_list != self.file_list:
                if self.debug:
                    self.diff_list(new_file_list, self.file_list)
                self.run_tests()
                self.file_list = new_file_list

def main(prog_args=None):
    """
    What do you expect?
    """
    if prog_args is None:
        prog_args = sys.argv

    parser = optparse.OptionParser()
    parser.usage = """Usage: %[prog] [options] [<path>]"""
    parser.add_option("-t", "--test-program", dest="test_program",
        default="nose", help="""specifies the test-program to use. Valid
        values include `nose` (or `nosetests`), `django` and `py` (for `py.test`)""")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
        default=False)
    parser.add_option('-s', '--size-max', dest='size_max', default=25, type="int",
        help="Sets the maximum size (in MB) of files.")
    parser.add_option('-c', '--custom-command', dest='custom_command',
        default=None, help="Specifies the test command to run."
        "\nBIG FAT WARNING: This will run a shell command. Use it at your own"
        "risks!!!"
        "\nIf the program deletes your whole project, it'll be you fault!")

    opt, args = parser.parse_args(prog_args)

    if opt.custom_command:
        answer = raw_input(
            'BIG FAT WARNING! You are about to run the command\n\n   $ %s\n\n'
            "Every time any file will be added/deleted/edited in your project."
            "\nYou must be aware that any shell command automatically ran may"
            "erase or corrupt your files."
            "\nUSE VERY CAREFULLY!!!"
            "\nNow that you've been warned, do you still want to go on? [y/N] " %
            opt.custom_command
        )
        if not answer.startswith('y'):
            sys.exit("Ok, bye...")


    if args[1:]:
        path = args[1]
    else:
        path = '.'

    try:
        watcher = Watcher(path, opt.test_program, opt.debug, opt.custom_command)
        agree = True
        watcher_file_size = watcher.file_sizes()
        if watcher_file_size > opt.size_max:
            answer = raw_input(
            "It looks like the total file size (%dMb) is larger than the `max size` option (%dMb)."
            "\nThis may slow down the file comparison process, and thus the daemon performance."
            "\nDo you wish to continue? [y/N] "  % (watcher_file_size, opt.size_max)).lower()
            if not answer.startswith('y'):
                agree = False

        if agree:
            print "Ready to watch file changes..."
            watcher.loop()
    except Exception, e:
        print e

    print "Bye"

if __name__ == '__main__':
    main()

