#!/usr/bin/env python

import sys
if len(sys.argv)>1 and sys.argv[1].lower() == 'gevent':
    from gevent import monkey
    monkey.patch_all()

import os
import logging
import unittest
import distutils.core

from glob import glob
from os.path import splitext, basename, join as pjoin


def run_tests():
    """
    Find and run all tests in the tests/ directory.

    Excludes live tests (tests/live_*).
    """
    testfiles = ['tests.test_overall']
    exclude = ['__init__.py', 'test_overall.py']
    for t in glob(pjoin('tests', '*.py')):
        if True not in [t.endswith(ex) for ex in exclude]:
            if basename(t).startswith('test_'):
                testfiles.append('tests.%s' % splitext(basename(t))[0])

    suites = []
    for file in testfiles:
        __import__(file)
        suites.append(sys.modules[file].suite)

    tests = unittest.TestSuite(suites)
    runner = unittest.TextTestRunner(verbosity=2)

    # Disable logging output
    logging.basicConfig(level=100)
    logging.disable(100)

    result = runner.run(tests)
    return result


# Add a 'test' command for setup.py

class TestCommand(distutils.core.Command):

    user_options = [ ]

    def initialize_options(self):
        self._dir = os.getcwd()

    def finalize_options(self):
        pass

    def run(self):
        run_tests()


if __name__ == '__main__':
    result = run_tests()
    print("<tests %s ran='%s' errors='%s' fails='%s' success='%s' gevent_enabled=%s/>" % (
        "xmlns='http//andyet.net/protocol/tests'",
        result.testsRun, len(result.errors),
        len(result.failures), result.wasSuccessful(),'gevent' in sys.modules))
