import unittest

class testevents(unittest.TestCase):

	def setUp(self):
		import sleekxmpp.stanza.presence as p
		self.p = p
	
	def testEventHappening(self):
		"Test handler working"
		import sleekxmpp
		c = sleekxmpp.ClientXMPP('crap@wherever', 'password')
		happened = []
		def handletestevent(event):
			happened.append(True)
		c.add_event_handler("test_event", handletestevent)
		c.event("test_event", {})
		c.event("test_event", {})
		self.failUnless(happened == [True, True], "event did not get triggered twice")
	
	def testDelEvent(self):
		"Test handler working, then deleted and not triggered"
		import sleekxmpp
		c = sleekxmpp.ClientXMPP('crap@wherever', 'password')
		happened = []
		def handletestevent(event):
			happened.append(True)
		c.add_event_handler("test_event", handletestevent)
		c.event("test_event", {})
		c.del_event_handler("test_event", handletestevent)
		c.event("test_event", {}) # should not trigger because it was deleted
		self.failUnless(happened == [True], "event did not get triggered the correct number of times")
        

suite = unittest.TestLoader().loadTestsFromTestCase(testevents)
