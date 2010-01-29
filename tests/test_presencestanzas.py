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

suite = unittest.TestLoader().loadTestsFromTestCase(testpresencestanzas)
