import unittest

class testmessagestanzas(unittest.TestCase):

	def setUp(self):
		import sleekxmpp.stanza.message as m
		self.m = m
	
	def testGroupchatReplyRegression(self):
		"Regression groupchat reply should be to barejid"
		msg = self.m.Message()
		msg['to'] = 'me@myserver.tld'
		msg['from'] = 'room@someservice.someserver.tld/somenick'
		msg['type'] = 'groupchat'
		msg['body'] = "this is a message"
		msg.reply()
		self.failUnless(str(msg['to']) == 'room@someservice.someserver.tld')

	def testAttribProperty(self):
		"Test attrib property returning self"
		msg = self.m.Message()
		msg.attrib.attrib.attrib['to'] = 'usr@server.tld'
		self.failUnless(str(msg['to']) == 'usr@server.tld')

suite = unittest.TestLoader().loadTestsFromTestCase(testmessagestanzas)
