import unittest
from xml.etree import cElementTree as ET
from sleekxmpp.xmlstream.matcher.stanzapath import StanzaPath
from . import xmlcompare

import sleekxmpp.plugins.xep_0030 as sd

def stanzaPlugin(stanza, plugin):                                                                       
	stanza.plugin_attrib_map[plugin.plugin_attrib] = plugin                                             
	stanza.plugin_tag_map["{%s}%s" % (plugin.namespace, plugin.name)] = plugin 

class testdisco(unittest.TestCase):

    def setUp(self):
        self.sd = sd
        stanzaPlugin(self.sd.Iq, self.sd.DiscoInfo)
        stanzaPlugin(self.sd.Iq, self.sd.DiscoItems)

    def try3Methods(self, xmlstring, iq):
	iq2 = self.sd.Iq(None, self.sd.ET.fromstring(xmlstring))
	values = iq2.getValues()
	iq3 = self.sd.Iq()
	iq3.setValues(values)
        self.failUnless(xmlstring == str(iq) == str(iq2) == str(iq3), str(iq)+"3 methods for creating stanza don't match")
        
    def testCreateInfoQueryNoNode(self):
        """Testing disco#info query with no node."""
        iq = self.sd.Iq()
        iq['id'] = "0"
        iq['disco_info']['node'] = ''
        xmlstring = """<iq id="0"><query xmlns="http://jabber.org/protocol/disco#info" /></iq>"""
	self.try3Methods(xmlstring, iq)

    def testCreateInfoQueryWithNode(self):
        """Testing disco#info query with a node."""
        iq = self.sd.Iq()
        iq['id'] = "0"
        iq['disco_info']['node'] = 'foo'
        xmlstring = """<iq id="0"><query xmlns="http://jabber.org/protocol/disco#info" node="foo" /></iq>"""
	self.try3Methods(xmlstring, iq)

    def testCreateInfoQueryNoNode(self):
        """Testing disco#items query with no node."""
        iq = self.sd.Iq()
        iq['id'] = "0"
        iq['disco_items']['node'] = ''
        xmlstring = """<iq id="0"><query xmlns="http://jabber.org/protocol/disco#items" /></iq>"""
	self.try3Methods(xmlstring, iq)

    def testCreateItemsQueryWithNode(self):
        """Testing disco#items query with a node."""
        iq = self.sd.Iq()
        iq['id'] = "0"
        iq['disco_items']['node'] = 'foo'
        xmlstring = """<iq id="0"><query xmlns="http://jabber.org/protocol/disco#items" node="foo" /></iq>"""
	self.try3Methods(xmlstring, iq)

    def testInfoIdentities(self):
        """Testing adding identities to disco#info."""
        iq = self.sd.Iq()
        iq['id'] = "0"
        iq['disco_info']['node'] = 'foo'
	iq['disco_info'].addIdentity('conference', 'text', 'Chatroom')
        xmlstring = """<iq id="0"><query xmlns="http://jabber.org/protocol/disco#info" node="foo"><identity category="conference" type="text" name="Chatroom" /></query></iq>"""
	self.try3Methods(xmlstring, iq)

    def testInfoFeatures(self):
        """Testing adding features to disco#info."""
        iq = self.sd.Iq()
        iq['id'] = "0"
        iq['disco_info']['node'] = 'foo'
	iq['disco_info'].addFeature('foo')
	iq['disco_info'].addFeature('bar')
        xmlstring = """<iq id="0"><query xmlns="http://jabber.org/protocol/disco#info" node="foo"><feature var="foo" /><feature var="bar" /></query></iq>"""
	self.try3Methods(xmlstring, iq)

    def testItems(self):
        """Testing adding features to disco#info."""
        iq = self.sd.Iq()
        iq['id'] = "0"
        iq['disco_items']['node'] = 'foo'
	iq['disco_items'].addItem('user@localhost')
	iq['disco_items'].addItem('user@localhost', 'foo')
	iq['disco_items'].addItem('user@localhost', 'bar', 'Testing')
        xmlstring = """<iq id="0"><query xmlns="http://jabber.org/protocol/disco#items" node="foo"><item jid="user@localhost" /><item node="foo" jid="user@localhost" /><item node="bar" jid="user@localhost" name="Testing" /></query></iq>"""
	self.try3Methods(xmlstring, iq)

    def testAddRemoveIdentities(self):
        """Test adding and removing identities to disco#info stanza"""
	ids = [('automation', 'commands', 'AdHoc'),
	       ('conference', 'text', 'ChatRoom')]

	info = self.sd.DiscoInfo()
	info.addIdentity(*ids[0])
	self.failUnless(info.getIdentities() == [ids[0]])

	info.delIdentity('automation', 'commands')
	self.failUnless(info.getIdentities() == [])

	info.setIdentities(ids)
	self.failUnless(info.getIdentities() == ids)

	info.delIdentity('automation', 'commands')
	self.failUnless(info.getIdentities() == [ids[1]])

	info.delIdentities()
	self.failUnless(info.getIdentities() == [])

    def testAddRemoveFeatures(self):
        """Test adding and removing features to disco#info stanza"""
	features = ['foo', 'bar', 'baz']

	info = self.sd.DiscoInfo()
	info.addFeature(features[0])
	self.failUnless(info.getFeatures() == [features[0]])

	info.delFeature('foo')
	self.failUnless(info.getFeatures() == [])

	info.setFeatures(features)
	self.failUnless(info.getFeatures() == features)

	info.delFeature('bar')
	self.failUnless(info.getFeatures() == ['foo', 'baz'])

	info.delFeatures()
	self.failUnless(info.getFeatures() == [])

    def testAddRemoveItems(self):
        """Test adding and removing items to disco#items stanza"""
	items = [('user@localhost', None, None),
		 ('user@localhost', 'foo', None),
		 ('user@localhost', 'bar', 'Test')]

	info = self.sd.DiscoItems()
	self.failUnless(True, ""+str(items[0]))

	info.addItem(*(items[0]))
	self.failUnless(info.getItems() == [items[0]], info.getItems())

	info.delItem('user@localhost')
	self.failUnless(info.getItems() == [])

	info.setItems(items)
	self.failUnless(info.getItems() == items)

	info.delItem('user@localhost', 'foo')
	self.failUnless(info.getItems() == [items[0], items[2]])

	info.delItems()
	self.failUnless(info.getItems() == [])
	

        
suite = unittest.TestLoader().loadTestsFromTestCase(testdisco)
