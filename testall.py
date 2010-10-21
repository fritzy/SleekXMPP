#!/usr/bin/env python
import unittest
import logging
import sys
import os

class testoverall(unittest.TestCase):

	def testModules(self):
		"""Testing all modules by compiling them"""
		import compileall
		import re
		if sys.version_info < (3,0):
			self.failUnless(compileall.compile_dir('.' + os.sep + 'sleekxmpp', rx=re.compile('/[.]svn'), quiet=True))
		else:
			self.failUnless(compileall.compile_dir('.' + os.sep + 'sleekxmpp', rx=re.compile('/[.]svn|.*26.*'), quiet=True))

	def	testTabNanny(self):
		"""Invoking the tabnanny"""
		import tabnanny
		self.failIf(tabnanny.check("." + os.sep + 'sleekxmpp'))
		#raise "Help!"

	def disabled_testMethodLength(self):
		"""Testing for excessive method lengths"""
		import re
		dirs = os.walk(sys.path[0] + os.sep + 'sleekxmpp')
		offenders = []
		for d in dirs:
			if not '.svn' in d[0]:
				for filename in d[2]:
					if filename.endswith('.py') and d[0].find("template%stemplates" % os.sep) == -1:
						with open("%s%s%s" % (d[0],os.sep,filename), "r") as fp:
							cur = None
							methodline = lineno = methodlen = methodindent = 0
							for line in fp:
								indentlevel = re.compile("^[\t ]*").search(line).end()
								line = line.expandtabs()
								lineno += 1
								if line.strip().startswith("def ") or line.strip().startswith("except") or (line.strip() and methodindent > indentlevel) or (line.strip() and methodindent == indentlevel): #new method found or old one ended
									if cur: #existing method needs final evaluation
										if methodlen > 50 and not cur.strip().startswith("def setupUi"):
											offenders.append("Method '%s' on line %s of %s/%s is longer than 50 lines (%s)" % (cur.strip(),methodline,d[0][len(rootp):],filename,methodlen))
										methodlen = 0
									cur = line
									methodindent = indentlevel
									methodline = lineno
								if line and cur and not line.strip().startswith("#") and not (cur.strip().startswith("try:") and methodindent == 0): #if we weren't all whitespace and weren't a comment
									methodlen += 1
		self.failIf(offenders,"\n".join(offenders))
			

if __name__ == '__main__':
	logging.basicConfig(level=100)
	logging.disable(100)
	#this doesn't need to be very clean
	alltests = [unittest.TestLoader().loadTestsFromTestCase(testoverall)]
	rootp = sys.path[0] + os.sep + 'tests'
	dirs = os.walk(rootp)
	for d in dirs:
		if not '.svn' in d[0]:
			for filename in d[2]:
				if filename.startswith('test_') and filename.endswith('.py'):
					modname = ('tests' + "." + filename)[:-3].replace(os.sep,'.')
					__import__(modname)
					#sys.modules[modname].config = moduleconfig
					alltests.append(sys.modules[modname].suite)
	alltests_suite = unittest.TestSuite(alltests)
	result = unittest.TextTestRunner(verbosity=2).run(alltests_suite)
	print("""<tests xmlns='http://andyet.net/protocol/tests' ran='%s' errors='%s' fails='%s' success='%s' />""" % (result.testsRun, len(result.errors), len(result.failures), result.wasSuccessful()))
