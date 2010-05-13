import unittest

class testpresencestanzas(unittest.TestCase):

	def setUp(self):
		import sleekxmpp.stanza.presence as p
		self.p = p
	
	def testPresenceShowRegression(self):
		"Regression check presence['type'] = 'dnd' show value working"
		p = self.p.Presence()
		p['type'] = 'dnd'
		self.failUnless(str(p) == "<presence><show>dnd</show></presence>")
	
	def testPresenceUnsolicitedOffline(self):
		"Unsolicted offline presence does not spawn changed_status or update roster"
		p = self.p.Presence()
		p['type'] = 'unavailable'
		p['from'] = 'bill@chadmore.com/gmail15af'
		import sleekxmpp
		c = sleekxmpp.ClientXMPP('crap@wherever', 'password')
		happened = []
		def handlechangedpresence(event):
			happened.append(True)
		c.add_event_handler("changed_status", handlechangedpresence)
		c._handlePresence(p)
		self.failUnless(happened == [], "changed_status event triggered for superfulous unavailable presence")
		self.failUnless(c.roster == {}, "Roster updated for superfulous unavailable presence")
        

suite = unittest.TestLoader().loadTestsFromTestCase(testpresencestanzas)
