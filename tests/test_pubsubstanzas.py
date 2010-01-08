import unittest

class testpubsubstanzas(unittest.TestCase):

	def setUp(self):
		import sleekxmpp.plugins.stanza_pubsub as ps
		self.ps = ps

	def testAffiliations(self):
		"Testing iq/pubsub/affiliations/affiliation stanzas"
		iq = self.ps.Iq()
		aff1 = self.ps.Affiliation()
		aff1['node'] = 'testnode'
		aff1['affiliation'] = 'owner'
		aff2 = self.ps.Affiliation()
		aff2['node'] = 'testnode2'
		aff2['affiliation'] = 'publisher'
		iq['pubsub']['affiliations'].append(aff1)
		iq['pubsub']['affiliations'].append(aff2)
		xmlstring = """<iq id="0"><pubsub xmlns="http://jabber.org/protocol/pubsub"><affiliations><affiliation node="testnode" affiliation="owner" /><affiliation node="testnode2" affiliation="publisher" /></affiliations></pubsub></iq>"""
		iq2 = self.ps.Iq(None, self.ps.ET.fromstring(xmlstring))
		iq3 = self.ps.Iq()
		values = iq2.getValues()
		iq3.setValues(values)
		self.failUnless(xmlstring == str(iq) == str(iq2) == str(iq3))
	

suite = unittest.TestLoader().loadTestsFromTestCase(testpubsubstanzas)
