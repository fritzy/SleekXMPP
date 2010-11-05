from sleekxmpp.test import *
import sleekxmpp.plugins.xep_0030 as xep_0030


class TestDisco(SleekTest):

    def setUp(self):
        register_stanza_plugin(Iq, xep_0030.DiscoInfo)
        register_stanza_plugin(Iq, xep_0030.DiscoItems)

    def testCreateInfoQueryNoNode(self):
        """Testing disco#info query with no node."""
        iq = self.Iq()
        iq['id'] = "0"
        iq['disco_info']['node'] = ''

        self.check(iq, """
          <iq id="0">
            <query xmlns="http://jabber.org/protocol/disco#info" />
          </iq>
        """)

    def testCreateInfoQueryWithNode(self):
        """Testing disco#info query with a node."""
        iq = self.Iq()
        iq['id'] = "0"
        iq['disco_info']['node'] = 'foo'

        self.check(iq, """
          <iq id="0">
            <query xmlns="http://jabber.org/protocol/disco#info" node="foo" />
          </iq>
        """)

    def testCreateInfoQueryNoNode(self):
        """Testing disco#items query with no node."""
        iq = self.Iq()
        iq['id'] = "0"
        iq['disco_items']['node'] = ''

        self.check(iq, """
          <iq id="0">
            <query xmlns="http://jabber.org/protocol/disco#items" />
          </iq>
        """)

    def testCreateItemsQueryWithNode(self):
        """Testing disco#items query with a node."""
        iq = self.Iq()
        iq['id'] = "0"
        iq['disco_items']['node'] = 'foo'

        self.check(iq, """
          <iq id="0">
            <query xmlns="http://jabber.org/protocol/disco#items" node="foo" />
          </iq>
        """)

    def testInfoIdentities(self):
        """Testing adding identities to disco#info."""
        iq = self.Iq()
        iq['id'] = "0"
        iq['disco_info']['node'] = 'foo'
        iq['disco_info'].addIdentity('conference', 'text', 'Chatroom')

        self.check(iq, """
          <iq id="0">
            <query xmlns="http://jabber.org/protocol/disco#info" node="foo">
              <identity category="conference" type="text" name="Chatroom" />
            </query>
          </iq>
        """)

    def testInfoFeatures(self):
        """Testing adding features to disco#info."""
        iq = self.Iq()
        iq['id'] = "0"
        iq['disco_info']['node'] = 'foo'
        iq['disco_info'].addFeature('foo')
        iq['disco_info'].addFeature('bar')

        self.check(iq, """
          <iq id="0">
            <query xmlns="http://jabber.org/protocol/disco#info" node="foo">
              <feature var="foo" />
              <feature var="bar" />
            </query>
          </iq>
        """)

    def testItems(self):
        """Testing adding features to disco#info."""
        iq = self.Iq()
        iq['id'] = "0"
        iq['disco_items']['node'] = 'foo'
        iq['disco_items'].addItem('user@localhost')
        iq['disco_items'].addItem('user@localhost', 'foo')
        iq['disco_items'].addItem('user@localhost', 'bar', 'Testing')

        self.check(iq, """
          <iq id="0">
            <query xmlns="http://jabber.org/protocol/disco#items" node="foo">
              <item jid="user@localhost" />
              <item node="foo" jid="user@localhost" />
              <item node="bar" jid="user@localhost" name="Testing" />
            </query>
          </iq>
        """)

    def testAddRemoveIdentities(self):
        """Test adding and removing identities to disco#info stanza"""
        ids = [('automation', 'commands', 'AdHoc'),
               ('conference', 'text', 'ChatRoom')]

        info = xep_0030.DiscoInfo()
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

        info = xep_0030.DiscoInfo()
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

        info = xep_0030.DiscoItems()
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


suite = unittest.TestLoader().loadTestsFromTestCase(TestDisco)
