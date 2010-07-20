import sleekxmpp
from sleektest import *
from sleekxmpp.stanza.presence import Presence

class TestPresenceStanzas(SleekTest):
	
        def testPresenceShowRegression(self):
		"""Regression check presence['type'] = 'dnd' show value working"""
		p = self.Presence()
		p['type'] = 'dnd'
		self.checkPresence(p, """
                  <presence><show>dnd</show></presence>
                """)

        def testPresenceType(self):
		"""Test manipulating presence['type']"""
		p = self.Presence()
		p['type'] = 'available'
		self.checkPresence(p, """
                  <presence />
                """)
		self.failUnless(p['type'] == 'available', "Incorrect presence['type'] for type 'available'")

		for showtype in ['away', 'chat', 'dnd', 'xa']:
			p['type'] = showtype
			self.checkPresence(p, """
                          <presence><show>%s</show></presence>
                        """ % showtype)
			self.failUnless(p['type'] == showtype, "Incorrect presence['type'] for type '%s'" % showtype)

		p['type'] = None
		self.checkPresence(p, """
                  <presence />
                """)

	def testPresenceUnsolicitedOffline(self):
		"""Unsolicted offline presence does not spawn changed_status or update roster"""
		p = self.Presence()
		p['type'] = 'unavailable'
		p['from'] = 'bill@chadmore.com/gmail15af'
		
		c = sleekxmpp.ClientXMPP('crap@wherever', 'password')
		happened = []
		def handlechangedpresence(event):
			happened.append(True)
		c.add_event_handler("changed_status", handlechangedpresence)
		c._handlePresence(p)
		
		self.failUnless(happened == [], "changed_status event triggered for superfulous unavailable presence")
		self.failUnless(c.roster == {}, "Roster updated for superfulous unavailable presence")
        

suite = unittest.TestLoader().loadTestsFromTestCase(TestPresenceStanzas)
