import os
import re
import sys
import unittest
import tabnanny
import compileall

class TestOverall(unittest.TestCase):

    """
    Test overall package health by compiling and checking
    code style.
    """

    def testModules(self):
        """Testing all modules by compiling them"""
        src = '.%ssleekxmpp' % os.sep
        if sys.version_info < (3, 0):
            rx = re.compile('/[.]svn')
        else:
            rx = re.compile('/[.]svn|.*26.*')
        self.failUnless(compileall.compile_dir(src, rx=rx, quiet=True))

    def testTabNanny(self):
        """Testing that indentation is consistent"""
        self.failIf(tabnanny.check('..%ssleekxmpp' % os.sep))


suite = unittest.TestLoader().loadTestsFromTestCase(TestOverall)
