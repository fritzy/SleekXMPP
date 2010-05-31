import unittest
from xml.etree import cElementTree as ET
from sleekxmpp.xmlstream.matcher.stanzapath import StanzaPath
from . import xmlcompare

import sleekxmpp.plugins.xep_0085 as cs

def stanzaPlugin(stanza, plugin):                                                                       
	stanza.plugin_attrib_map[plugin.plugin_attrib] = plugin                                             
	stanza.plugin_tag_map["{%s}%s" % (plugin.namespace, plugin.name)] = plugin 

class testchatstates(unittest.TestCase):

	def setUp(self):
		self.cs = cs
		stanzaPlugin(self.cs.Message, self.cs.Active)
		stanzaPlugin(self.cs.Message, self.cs.Composing)
		stanzaPlugin(self.cs.Message, self.cs.Gone)
		stanzaPlugin(self.cs.Message, self.cs.Inactive)
		stanzaPlugin(self.cs.Message, self.cs.Paused)

	def try2Methods(self, xmlstring, msg):
		msg2 = self.cs.Message(None, self.cs.ET.fromstring(xmlstring))
		self.failUnless(xmlstring == str(msg) == str(msg2), 
				"Two methods for creating stanza don't match")
        
	def testCreateChatState(self):
		"""Testing creating chat states."""
		xmlstring = """<message><%s xmlns="http://jabber.org/protocol/chatstates" /></message>"""

		msg = self.cs.Message()
		msg['chat_state'].active()
		self.try2Methods(xmlstring % 'active', msg)

		msg['chat_state'].composing()
		self.try2Methods(xmlstring % 'composing', msg)

		msg['chat_state'].gone()
		self.try2Methods(xmlstring % 'gone', msg)

		msg['chat_state'].inactive()
		self.try2Methods(xmlstring % 'inactive', msg)

		msg['chat_state'].paused()
		self.try2Methods(xmlstring % 'paused', msg)

suite = unittest.TestLoader().loadTestsFromTestCase(testchatstates)
