import unittest
from xml.etree import cElementTree as ET
from sleekxmpp.xmlstream.matcher.stanzapath import StanzaPath
from . import xmlcompare

import sleekxmpp.plugins.xep_0033 as addr


def stanzaPlugin(stanza, plugin):
	stanza.plugin_attrib_map[plugin.plugin_attrib] = plugin
	stanza.plugin_tag_map["{%s}%s" % (plugin.namespace, plugin.name)] = plugin


class testaddresses(unittest.TestCase):
    	def setUp(self):
		self.addr = addr
                stanzaPlugin(self.addr.Message, self.addr.Addresses)

	def try2Methods(self, xmlstring, msg):
		msg2 = self.addr.Message(None, self.addr.ET.fromstring(xmlstring))
                self.failUnless(xmlstring == str(msg) == str(msg2),
				"""Three methods for creating stanza don't match:\n%s\n%s\n%s""" % (xmlstring, str(msg), str(msg2)))

        def testAddAddress(self):
		"""Testing adding extended stanza address."""
		xmlstring = """<message><addresses xmlns="http://jabber.org/protocol/address"><address jid="to@header1.org" type="to" /></addresses></message>"""

		msg = self.addr.Message()
		msg['addresses'].addAddress(atype='to', jid='to@header1.org')
		self.try2Methods(xmlstring, msg)

		xmlstring = """<message><addresses xmlns="http://jabber.org/protocol/address"><address jid="replyto@header1.org" type="replyto" desc="Reply address" /></addresses></message>"""

		msg = self.addr.Message()
		msg['addresses'].addAddress(atype='replyto', jid='replyto@header1.org', desc='Reply address')
		self.try2Methods(xmlstring, msg)

	def testAddAddresses(self):
		"""Testing adding multiple extended stanza addresses."""

		xmlstring = """<message><addresses xmlns="http://jabber.org/protocol/address"><address jid="replyto@header1.org" type="replyto" desc="Reply address" /><address jid="cc@header2.org" type="cc" /><address jid="bcc@header2.org" type="bcc" /></addresses></message>"""

		msg = self.addr.Message()
		msg['addresses'].setAddresses([{'type':'replyto', 'jid':'replyto@header1.org', 'desc':'Reply address'},
					       {'type':'cc', 'jid':'cc@header2.org'},
					       {'type':'bcc', 'jid':'bcc@header2.org'}])
		self.try2Methods(xmlstring, msg)

		msg = self.addr.Message()
		msg['addresses']['replyto'] = [{'jid':'replyto@header1.org', 'desc':'Reply address'}]
		msg['addresses']['cc'] = [{'jid':'cc@header2.org'}]
		msg['addresses']['bcc'] = [{'jid':'bcc@header2.org'}]
		self.try2Methods(xmlstring, msg)

	def testAddURI(self):
		"""Testing adding URI attribute to extended stanza address."""

		xmlstring = """<message><addresses xmlns="http://jabber.org/protocol/address"><address node="foo" jid="to@header1.org" type="to" /></addresses></message>"""
		msg = self.addr.Message()
		addr = msg['addresses'].addAddress(atype='to', jid='to@header1.org', node='foo')
		self.try2Methods(xmlstring, msg)

		xmlstring = """<message><addresses xmlns="http://jabber.org/protocol/address"><address type="to" uri="mailto:to@header2.org" /></addresses></message>"""
		addr['uri'] = 'mailto:to@header2.org'
		self.try2Methods(xmlstring, msg)

	def testDelivered(self):
		"""Testing delivered attribute of extended stanza addresses."""

		xmlstring = """<message><addresses xmlns="http://jabber.org/protocol/address"><address %sjid="to@header1.org" type="to" /></addresses></message>"""

		msg = self.addr.Message()
		addr = msg['addresses'].addAddress(jid='to@header1.org', atype='to')
		self.try2Methods(xmlstring % '', msg)

		addr['delivered'] = True
		self.try2Methods(xmlstring % 'delivered="true" ', msg)

		addr['delivered'] = False
		self.try2Methods(xmlstring % '', msg)


suite = unittest.TestLoader().loadTestsFromTestCase(testaddresses)
