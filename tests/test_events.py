import sleekxmpp
from sleektest import *


class TestEvents(SleekTest):
	
	def testEventHappening(self):
		"Test handler working"
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
		c = sleekxmpp.ClientXMPP('crap@wherever', 'password')
		happened = []
		def handletestevent(event):
			happened.append(True)
		c.add_event_handler("test_event", handletestevent)
		c.event("test_event", {})
		c.del_event_handler("test_event", handletestevent)
		c.event("test_event", {}) # should not trigger because it was deleted
		self.failUnless(happened == [True], "event did not get triggered the correct number of times")
        

suite = unittest.TestLoader().loadTestsFromTestCase(TestEvents)
