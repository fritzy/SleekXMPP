from sleekxmpp.plugins.stanza_pubsub import *

def testAffiliations():
	iq = Iq()
	aff1 = Affiliation()
	aff1['node'] = 'testnode'
	aff1['affiliation'] = 'owner'
	aff2 = Affiliation()
	aff2['node'] = 'testnode2'
	aff2['affiliation'] = 'publisher'
	iq['pubsub']['affiliations'].append(aff1)
	iq['pubsub']['affiliations'].append(aff2)
	print(iq)
	iq2 = Iq(None, ET.fromstring("""<iq id="0"><pubsub xmlns="http://jabber.org/protocol/pubsub"><affiliations><affiliation node="testnode" affiliation="owner" /><affiliation node="testnode2" affiliation="publisher" /></affiliations></pubsub></iq>"""))
	iq3 = Iq()
	values = iq2.getValues()
	print(values)
	iq3.setValues(values)
	print("-"*8)
	print(iq3.keys())

	print(iq3)
	print(str(iq) == str(iq2) == str(iq3))
	

testAffiliations()
