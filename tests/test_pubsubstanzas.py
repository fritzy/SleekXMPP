import unittest
from xml.etree import cElementTree as ET
from sleekxmpp.xmlstream.matcher.stanzapath import StanzaPath

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
		self.failUnless(xmlstring == str(iq) == str(iq2) == str(iq3), "3 methods for creating stanza don't match")
		self.failUnless(iq.match('iq@id=0/pubsub/affiliations/affiliation@node=testnode2@affiliation=publisher'), 'Match path failed')
	
	def testSubscriptions(self):
		"Testing iq/pubsub/subscriptions/subscription stanzas"
		iq = self.ps.Iq()
		sub1 = self.ps.Subscription()
		sub1['node'] = 'testnode'
		sub1['jid'] = 'steve@myserver.tld/someresource'
		sub2 = self.ps.Subscription()
		sub2['node'] = 'testnode2'
		sub2['jid'] = 'boogers@bork.top/bill'
		sub2['subscription'] = 'subscribed'
		iq['pubsub']['subscriptions'].append(sub1)
		iq['pubsub']['subscriptions'].append(sub2)
		xmlstring = """<iq id="0"><pubsub xmlns="http://jabber.org/protocol/pubsub"><subscriptions><subscription node="testnode" jid="steve@myserver.tld/someresource" /><subscription node="testnode2" jid="boogers@bork.top/bill" subscription="subscribed" /></subscriptions></pubsub></iq>"""
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
		"Testing iq/pubsub/items stanzas"
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
		"Testing iq/pubsub/create&configure stanzas"
		from sleekxmpp.plugins import xep_0004
		iq = self.ps.Iq()
		iq['pubsub']['create']['node'] = 'mynode'
		form = xep_0004.Form()
		form.addField('pubsub#title', ftype='text-single', value='This thing is awesome')
		iq['pubsub']['configure']['config'] = form
		xmlstring = """<iq id="0"><pubsub xmlns="http://jabber.org/protocol/pubsub"><create node="mynode" /><configure><x xmlns="jabber:x:data" type="form"><field var="pubsub#title" type="text-single"><value>This thing is awesome</value></field></x></configure></pubsub></iq>"""
		iq2 = self.ps.Iq(None, self.ps.ET.fromstring(xmlstring))
		iq3 = self.ps.Iq()
		values = iq2.getValues()
		iq3.setValues(values)
		self.failUnless(xmlstring == str(iq) == str(iq2) == str(iq3))
	
	def testDefault(self):
		"Testing iq/pubsub_owner/default stanzas"
		from sleekxmpp.plugins import xep_0004
		iq = self.ps.Iq()
		iq['pubsub_owner']['default']
		iq['pubsub_owner']['default']['node'] = 'mynode'
		form = xep_0004.Form()
		form.addField('pubsub#title', ftype='text-single', value='This thing is awesome')
		iq['pubsub_owner']['default']['config'] = form
		xmlstring = """<iq id="0"><pubsub xmlns="http://jabber.org/protocol/pubsub#owner"><default node="mynode"><x xmlns="jabber:x:data" type="form"><field var="pubsub#title" type="text-single"><value>This thing is awesome</value></field></x></default></pubsub></iq>"""
		iq2 = self.ps.Iq(None, self.ps.ET.fromstring(xmlstring))
		iq3 = self.ps.Iq()
		values = iq2.getValues()
		iq3.setValues(values)
		self.failUnless(xmlstring == str(iq) == str(iq2) == str(iq3))
	
	def testSubscribe(self):
		"Testing iq/pubsub/subscribe stanzas"
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
	
	def testPublish(self):
		"Testing iq/pubsub/publish stanzas"
		iq = self.ps.Iq()
		iq['pubsub']['publish']['node'] = 'thingers'
		payload = ET.fromstring("""<thinger xmlns="http://andyet.net/protocol/thinger" x="1" y='2'><child1 /><child2 normandy='cheese' foo='bar' /></thinger>""")
		payload2 = ET.fromstring("""<thinger2 xmlns="http://andyet.net/protocol/thinger2" x="12" y='22'><child12 /><child22 normandy='cheese2' foo='bar2' /></thinger2>""")
		item = self.ps.Item()
		item['id'] = 'asdf'
		item['payload'] = payload
		item2 = self.ps.Item()
		item2['id'] = 'asdf2'
		item2['payload'] = payload2
		iq['pubsub']['publish'].append(item)
		iq['pubsub']['publish'].append(item2)
		xmlstring = """<iq id="0"><pubsub xmlns="http://jabber.org/protocol/pubsub"><publish node="thingers"><item id="asdf"><thinger xmlns="http://andyet.net/protocol/thinger" y="2" x="1"><child1 /><child2 foo="bar" normandy="cheese" /></thinger></item><item id="asdf2"><thinger2 xmlns="http://andyet.net/protocol/thinger2" y="22" x="12"><child12 /><child22 foo="bar2" normandy="cheese2" /></thinger2></item></publish></pubsub></iq>"""
		iq2 = self.ps.Iq(None, self.ps.ET.fromstring(xmlstring))
		iq3 = self.ps.Iq()
		values = iq2.getValues()
		iq3.setValues(values)
		self.failUnless(xmlstring == str(iq) == str(iq2) == str(iq3))

	def testDelete(self):
		"Testing iq/pubsub_owner/delete stanzas"
		iq = self.ps.Iq()
		iq['pubsub_owner']['delete']['node'] = 'thingers'
		xmlstring = """<iq id="0"><pubsub xmlns="http://jabber.org/protocol/pubsub#owner"><delete node="thingers" /></pubsub></iq>"""
		iq2 = self.ps.Iq(None, self.ps.ET.fromstring(xmlstring))
		iq3 = self.ps.Iq()
		iq3.setValues(iq2.getValues())
		self.failUnless(xmlstring == str(iq) == str(iq2) == str(iq3))
	
	def testCreateConfigGet(self):
		"""Testing getting config from full create"""
		xml = """<iq to="pubsub.asdf" type="set" id="E" from="fritzy@asdf/87292ede-524d-4117-9076-d934ed3db8e7"><pubsub xmlns="http://jabber.org/protocol/pubsub"><create node="testnode2" /><configure><x xmlns="jabber:x:data" type="submit"><field var="FORM_TYPE" type="hidden"><value>http://jabber.org/protocol/pubsub#node_config</value></field><field var="pubsub#node_type" type="list-single" label="Select the node type"><value>leaf</value></field><field var="pubsub#title" type="text-single" label="A friendly name for the node" /><field var="pubsub#deliver_notifications" type="boolean" label="Deliver event notifications"><value>1</value></field><field var="pubsub#deliver_payloads" type="boolean" label="Deliver payloads with event notifications"><value>1</value></field><field var="pubsub#notify_config" type="boolean" label="Notify subscribers when the node configuration changes" /><field var="pubsub#notify_delete" type="boolean" label="Notify subscribers when the node is deleted" /><field var="pubsub#notify_retract" type="boolean" label="Notify subscribers when items are removed from the node"><value>1</value></field><field var="pubsub#notify_sub" type="boolean" label="Notify owners about new subscribers and unsubscribes" /><field var="pubsub#persist_items" type="boolean" label="Persist items in storage" /><field var="pubsub#max_items" type="text-single" label="Max # of items to persist"><value>10</value></field><field var="pubsub#subscribe" type="boolean" label="Whether to allow subscriptions"><value>1</value></field><field var="pubsub#access_model" type="list-single" label="Specify the subscriber model"><value>open</value></field><field var="pubsub#publish_model" type="list-single" label="Specify the publisher model"><value>publishers</value></field><field var="pubsub#send_last_published_item" type="list-single" label="Send last published item"><value>never</value></field><field var="pubsub#presence_based_delivery" type="boolean" label="Deliver notification only to available users" /></x></configure></pubsub></iq>"""
		iq = self.ps.Iq(None, self.ps.ET.fromstring(xml))
		config = iq['pubsub']['configure']['config']
		self.failUnless(config.getValues() != {})

suite = unittest.TestLoader().loadTestsFromTestCase(testpubsubstanzas)
