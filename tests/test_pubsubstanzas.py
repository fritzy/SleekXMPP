import unittest
from xml.etree import cElementTree as ET

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
	
	def testSubscriptions(self):
		"Testing iq/pubsub/subscriptions/subscription stanzas"
		iq = self.ps.Iq()
		sub1 = self.ps.Subscription()
		sub1['node'] = 'testnode'
		sub1['jid'] = 'steve@myserver.tld/someresource'
		sub2 = self.ps.Subscription()
		sub2['node'] = 'testnode2'
		sub2['jid'] = 'boogers@bork.top/bill'
		iq['pubsub']['subscriptions'].append(sub1)
		iq['pubsub']['subscriptions'].append(sub2)
		xmlstring = """<iq id="0"><pubsub xmlns="http://jabber.org/protocol/pubsub"><subscriptions><subscription node="testnode" jid="steve@myserver.tld/someresource" /><subscription node="testnode2" jid="boogers@bork.top/bill" /></subscriptions></pubsub></iq>"""
		iq2 = self.ps.Iq(None, self.ps.ET.fromstring(xmlstring))
		iq3 = self.ps.Iq()
		values = iq2.getValues()
		iq3.setValues(values)
		self.failUnless(xmlstring == str(iq) == str(iq2) == str(iq3))
	
	def testOptionalSettings(self):
		"Testing iq/pubsub/subscription/subscribe-options stanzas"
		iq = self.ps.Iq()
		iq['pubsub']['subscription']['suboptions']['required'] = True
		iq['pubsub']['subscription']['node'] = 'testnode alsdkjfas'
		iq['pubsub']['subscription']['jid'] = "fritzy@netflint.net/sleekxmpp"
		iq['pubsub']['subscription']['subscription'] = 'unconfigured'
		xmlstring = """<iq id="0"><pubsub xmlns="http://jabber.org/protocol/pubsub"><subscription node="testnode alsdkjfas" jid="fritzy@netflint.net/sleekxmpp" subscription="unconfigured"><subscribe-options><required /></subscribe-options></subscription></pubsub></iq>"""
		iq2 = self.ps.Iq(None, self.ps.ET.fromstring(xmlstring))
		iq3 = self.ps.Iq()
		values = iq2.getValues()
		iq3.setValues(values)
		self.failUnless(xmlstring == str(iq) == str(iq2) == str(iq3))
	
	def testItems(self):
		iq = self.ps.Iq()
		iq['pubsub']['items']
		payload = ET.fromstring("""<thinger xmlns="http://andyet.net/protocol/thinger" x="1" y='2'><child1 /><child2 normandy='cheese' foo='bar' /></thinger>""")
		payload2 = ET.fromstring("""<thinger2 xmlns="http://andyet.net/protocol/thinger2" x="12" y='22'><child12 /><child22 normandy='cheese2' foo='bar2' /></thinger2>""")
		item = self.ps.Item()
		item['id'] = 'asdf'
		item['payload'] = payload
		item2 = self.ps.Item()
		item2['id'] = 'asdf2'
		item2['payload'] = payload2
		iq['pubsub']['items'].append(item)
		iq['pubsub']['items'].append(item2)
		xmlstring = """<iq id="0"><pubsub xmlns="http://jabber.org/protocol/pubsub"><items><item id="asdf"><thinger xmlns="http://andyet.net/protocol/thinger" y="2" x="1"><child1 /><child2 foo="bar" normandy="cheese" /></thinger></item><item id="asdf2"><thinger2 xmlns="http://andyet.net/protocol/thinger2" y="22" x="12"><child12 /><child22 foo="bar2" normandy="cheese2" /></thinger2></item></items></pubsub></iq>"""
		iq2 = self.ps.Iq(None, self.ps.ET.fromstring(xmlstring))
		iq3 = self.ps.Iq()
		values = iq2.getValues()
		iq3.setValues(values)
		self.failUnless(xmlstring == str(iq) == str(iq2) == str(iq3))
		
	def testCreate(self):
		from sleekxmpp.plugins import xep_0004
		iq = self.ps.Iq()
		iq['pubsub']['create']['configure']
		iq['pubsub']['create']['node'] = 'mynode'
		form = xep_0004.Form()
		form.addField('pubsub#title', ftype='text-single', value='This thing is awesome')
		iq['pubsub']['create']['configure']['config'] = form
		xmlstring = """<iq id="0"><pubsub xmlns="http://jabber.org/protocol/pubsub"><create node="mynode"><configure><x xmlns="jabber:x:data" type="form"><field var="pubsub#title" type="text-single"><value>This thing is awesome</value></field></x></configure></create></pubsub></iq>"""
		iq2 = self.ps.Iq(None, self.ps.ET.fromstring(xmlstring))
		iq3 = self.ps.Iq()
		values = iq2.getValues()
		iq3.setValues(values)
		self.failUnless(xmlstring == str(iq) == str(iq2) == str(iq3))
	
	def testDefault(self):
		from sleekxmpp.plugins import xep_0004
		iq = self.ps.Iq()
		iq['pubsub']['default']
		iq['pubsub']['default']['node'] = 'mynode'
		form = xep_0004.Form()
		form.addField('pubsub#title', ftype='text-single', value='This thing is awesome')
		iq['pubsub']['default']['config'] = form
		xmlstring = """<iq id="0"><pubsub xmlns="http://jabber.org/protocol/pubsub"><default node="mynode"><x xmlns="jabber:x:data" type="form"><field var="pubsub#title" type="text-single"><value>This thing is awesome</value></field></x></default></pubsub></iq>"""
		iq2 = self.ps.Iq(None, self.ps.ET.fromstring(xmlstring))
		iq3 = self.ps.Iq()
		values = iq2.getValues()
		iq3.setValues(values)
		self.failUnless(xmlstring == str(iq) == str(iq2) == str(iq3))
	
	def testSubscribe(self):
		from sleekxmpp.plugins import xep_0004
		iq = self.ps.Iq()
		iq['pubsub']['subscribe']['options']
		iq['pubsub']['subscribe']['node'] = 'cheese'
		iq['pubsub']['subscribe']['jid'] = 'fritzy@netflint.net/sleekxmpp'
		iq['pubsub']['subscribe']['options']['node'] = 'cheese'
		iq['pubsub']['subscribe']['options']['jid'] = 'fritzy@netflint.net/sleekxmpp'
		form = xep_0004.Form()
		form.addField('pubsub#title', ftype='text-single', value='This thing is awesome')
		iq['pubsub']['subscribe']['options']['options'] = form
		xmlstring = """<iq id="0"><pubsub xmlns="http://jabber.org/protocol/pubsub"><subscribe node="cheese" jid="fritzy@netflint.net/sleekxmpp"><options node="cheese" jid="fritzy@netflint.net/sleekxmpp"><x xmlns="jabber:x:data" type="form"><field var="pubsub#title" type="text-single"><value>This thing is awesome</value></field></x></options></subscribe></pubsub></iq>"""
		iq2 = self.ps.Iq(None, self.ps.ET.fromstring(xmlstring))
		iq3 = self.ps.Iq()
		values = iq2.getValues()
		iq3.setValues(values)
		self.failUnless(xmlstring == str(iq) == str(iq2) == str(iq3))

suite = unittest.TestLoader().loadTestsFromTestCase(testpubsubstanzas)
