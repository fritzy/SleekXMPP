import unittest
from sleekxmpp import Iq
from sleekxmpp.test import SleekTest
import sleekxmpp.plugins.xep_0030 as xep_0030
from sleekxmpp.xmlstream import register_stanza_plugin


class TestDisco(SleekTest):

    """
    Test creating and manipulating the disco#info and
    disco#items stanzas from the XEP-0030 plugin.
    """

    def setUp(self):
        register_stanza_plugin(Iq, xep_0030.DiscoInfo)
        register_stanza_plugin(Iq, xep_0030.DiscoItems)

    def testCreateInfoQueryNoNode(self):
        """Testing disco#info query with no node."""
        iq = self.Iq()
        iq['disco_info']['node'] = ''

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info" />
          </iq>
        """)

    def testCreateInfoQueryWithNode(self):
        """Testing disco#info query with a node."""
        iq = self.Iq()
        iq['disco_info']['node'] = 'foo'

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="foo" />
          </iq>
        """)

    def testCreateItemsQueryNoNode(self):
        """Testing disco#items query with no node."""
        iq = self.Iq()
        iq['disco_items']['node'] = ''

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#items" />
          </iq>
        """)

    def testCreateItemsQueryWithNode(self):
        """Testing disco#items query with a node."""
        iq = self.Iq()
        iq['disco_items']['node'] = 'foo'

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#items"
                   node="foo" />
          </iq>
        """)

    def testIdentities(self):
        """Testing adding identities to disco#info."""
        iq = self.Iq()
        iq['disco_info'].add_identity('conference', 'text',
                                      name='Chatroom',
                                      lang='en')

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info">
              <identity category="conference"
                        type="text"
                        name="Chatroom"
                        xml:lang="en" />
            </query>
          </iq>
        """)

    def testDuplicateIdentities(self):
        """
        Test adding multiple copies of the same category
        and type combination. Only the first identity should
        be kept.
        """
        iq = self.Iq()
        iq['disco_info'].add_identity('conference', 'text',
                                      name='Chatroom')
        iq['disco_info'].add_identity('conference', 'text',
                                      name='MUC')
        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info">
              <identity category="conference"
                        type="text"
                        name="Chatroom" />
            </query>
          </iq>
        """)

    def testDuplicateIdentitiesWithLangs(self):
        """
        Test adding multiple copies of the same category,
        type, and language combination. Only the first identity
        should be kept.
        """
        iq = self.Iq()
        iq['disco_info'].add_identity('conference', 'text',
                                      name='Chatroom',
                                      lang='en')
        iq['disco_info'].add_identity('conference', 'text',
                                      name='MUC',
                                      lang='en')
        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info">
              <identity category="conference"
                        type="text"
                        name="Chatroom"
                        xml:lang="en" />
            </query>
          </iq>
        """)

    def testRemoveIdentitiesNoLang(self):
        """Test removing identities from a disco#info stanza."""
        iq = self.Iq()
        iq['disco_info'].add_identity('client', 'pc')
        iq['disco_info'].add_identity('client', 'bot')

        iq['disco_info'].del_identity('client', 'pc')

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info">
              <identity category="client" type="bot" />
            </query>
          </iq>
        """)

    def testRemoveIdentitiesWithLang(self):
        """Test removing identities from a disco#info stanza."""
        iq = self.Iq()
        iq['disco_info'].add_identity('client', 'pc')
        iq['disco_info'].add_identity('client', 'bot')
        iq['disco_info'].add_identity('client', 'pc', lang='no')

        iq['disco_info'].del_identity('client', 'pc')

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info">
              <identity category="client" type="bot" />
              <identity category="client"
                        type="pc"
                        xml:lang="no" />
            </query>
          </iq>
        """)

    def testRemoveAllIdentitiesNoLang(self):
        """Test removing all identities from a disco#info stanza."""
        iq = self.Iq()
        iq['disco_info'].add_identity('client', 'bot', name='Bot')
        iq['disco_info'].add_identity('client', 'bot', lang='no')
        iq['disco_info'].add_identity('client', 'console')

        del iq['disco_info']['identities']

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info" />
          </iq>
        """)

    def testRemoveAllIdentitiesWithLang(self):
        """Test removing all identities from a disco#info stanza."""
        iq = self.Iq()
        iq['disco_info'].add_identity('client', 'bot', name='Bot')
        iq['disco_info'].add_identity('client', 'bot', lang='no')
        iq['disco_info'].add_identity('client', 'console')

        iq['disco_info'].del_identities(lang='no')

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info">
              <identity category="client" type="bot" name="Bot" />
              <identity category="client" type="console" />
            </query>
          </iq>
        """)

    def testAddBatchIdentitiesNoLang(self):
        """Test adding multiple identities at once to a disco#info stanza."""
        iq = self.Iq()
        identities = [('client', 'pc', 'no', 'PC Client'),
                      ('client', 'bot', None, 'Bot'),
                      ('client', 'console', None, None)]

        iq['disco_info']['identities'] = identities

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info">
              <identity category="client"
                        type="pc"
                        xml:lang="no"
                        name="PC Client" />
              <identity category="client" type="bot" name="Bot" />
              <identity category="client" type="console" />
            </query>
          </iq>
        """)


    def testAddBatchIdentitiesWithLang(self):
        """Test selectively replacing identities based on language."""
        iq = self.Iq()
        iq['disco_info'].add_identity('client', 'pc', lang='no')
        iq['disco_info'].add_identity('client', 'pc', lang='en')
        iq['disco_info'].add_identity('client', 'pc', lang='fr')

        identities = [('client', 'bot', 'fr', 'Bot'),
                      ('client', 'bot', 'en', 'Bot')]

        iq['disco_info'].set_identities(identities, lang='fr')

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info">
              <identity category="client" type="pc" xml:lang="no" />
              <identity category="client" type="pc" xml:lang="en" />
              <identity category="client"
                        type="bot"
                        xml:lang="fr"
                        name="Bot" />
              <identity category="client"
                        type="bot"
                        xml:lang="en"
                        name="Bot" />
            </query>
          </iq>
        """)

    def testGetIdentitiesNoLang(self):
        """Test getting all identities from a disco#info stanza."""
        iq = self.Iq()
        iq['disco_info'].add_identity('client', 'pc')
        iq['disco_info'].add_identity('client', 'pc', lang='no')
        iq['disco_info'].add_identity('client', 'pc', lang='en')
        iq['disco_info'].add_identity('client', 'pc', lang='fr')

        expected = set([('client', 'pc', None, None),
                        ('client', 'pc', 'no', None),
                        ('client', 'pc', 'en', None),
                        ('client', 'pc', 'fr', None)])
        self.failUnless(iq['disco_info']['identities'] == expected,
                "Identities do not match:\n%s\n%s" % (
                    expected,
                    iq['disco_info']['identities']))

    def testGetIdentitiesWithLang(self):
        """
        Test getting all identities of a given
        lang from a disco#info stanza.
        """
        iq = self.Iq()
        iq['disco_info'].add_identity('client', 'pc')
        iq['disco_info'].add_identity('client', 'pc', lang='no')
        iq['disco_info'].add_identity('client', 'pc', lang='en')
        iq['disco_info'].add_identity('client', 'pc', lang='fr')

        expected = set([('client', 'pc', 'no', None)])
        result = iq['disco_info'].get_identities(lang='no')
        self.failUnless(result == expected,
                "Identities do not match:\n%s\n%s" % (
                    expected, result))

    def testFeatures(self):
        """Testing adding features to disco#info."""
        iq = self.Iq()
        iq['disco_info'].add_feature('foo')
        iq['disco_info'].add_feature('bar')

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info">
              <feature var="foo" />
              <feature var="bar" />
            </query>
          </iq>
        """)

    def testFeaturesDuplicate(self):
        """Test adding duplicate features to disco#info."""
        iq = self.Iq()
        iq['disco_info'].add_feature('foo')
        iq['disco_info'].add_feature('bar')
        iq['disco_info'].add_feature('foo')

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info">
              <feature var="foo" />
              <feature var="bar" />
            </query>
          </iq>
        """)

    def testRemoveFeature(self):
        """Test removing a feature from disco#info."""
        iq = self.Iq()
        iq['disco_info'].add_feature('foo')
        iq['disco_info'].add_feature('bar')
        iq['disco_info'].add_feature('baz')

        iq['disco_info'].del_feature('foo')

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info">
              <feature var="bar" />
              <feature var="baz" />
            </query>
          </iq>
        """)

    def testGetFeatures(self):
        """Test getting all features from a disco#info stanza."""
        iq = self.Iq()
        iq['disco_info'].add_feature('foo')
        iq['disco_info'].add_feature('bar')
        iq['disco_info'].add_feature('baz')

        expected = set(['foo', 'bar', 'baz'])
        self.failUnless(iq['disco_info']['features'] == expected,
                "Features do not match:\n%s\n%s" % (
                    expected,
                    iq['disco_info']['features']))

    def testRemoveAllFeatures(self):
        """Test removing all features from a disco#info stanza."""
        iq = self.Iq()
        iq['disco_info'].add_feature('foo')
        iq['disco_info'].add_feature('bar')
        iq['disco_info'].add_feature('baz')

        del iq['disco_info']['features']

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info" />
          </iq>
        """)

    def testAddBatchFeatures(self):
        """Test adding multiple features at once to a disco#info stanza."""
        iq = self.Iq()
        features = ['foo', 'bar', 'baz']

        iq['disco_info']['features'] = features

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#info">
              <feature var="foo" />
              <feature var="bar" />
              <feature var="baz" />
            </query>
          </iq>
        """)

    def testItems(self):
        """Testing adding features to disco#info."""
        iq = self.Iq()
        iq['disco_items'].add_item('user@localhost')
        iq['disco_items'].add_item('user@localhost', 'foo')
        iq['disco_items'].add_item('user@localhost', 'bar', name='Testing')

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#items">
              <item jid="user@localhost" />
              <item jid="user@localhost"
                    node="foo" />
              <item jid="user@localhost"
                    node="bar"
                    name="Testing" />
            </query>
          </iq>
        """)

    def testDuplicateItems(self):
        """Test adding items with the same JID without any nodes."""
        iq = self.Iq()
        iq['disco_items'].add_item('user@localhost', name='First')
        iq['disco_items'].add_item('user@localhost', name='Second')

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#items">
              <item jid="user@localhost" name="First" />
            </query>
          </iq>
        """)


    def testDuplicateItemsWithNodes(self):
        """Test adding items with the same JID/node combination."""
        iq = self.Iq()
        iq['disco_items'].add_item('user@localhost',
                                   node='foo',
                                   name='First')
        iq['disco_items'].add_item('user@localhost',
                                   node='foo',
                                   name='Second')

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#items">
              <item jid="user@localhost" node="foo" name="First" />
            </query>
          </iq>
        """)

    def testRemoveItemsNoNode(self):
        """Test removing items without nodes from a disco#items stanza."""
        iq = self.Iq()
        iq['disco_items'].add_item('user@localhost')
        iq['disco_items'].add_item('user@localhost', node='foo')
        iq['disco_items'].add_item('test@localhost')

        iq['disco_items'].del_item('user@localhost')

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#items">
              <item jid="user@localhost" node="foo" />
              <item jid="test@localhost" />
            </query>
          </iq>
        """)

    def testRemoveItemsWithNode(self):
        """Test removing items with nodes from a disco#items stanza."""
        iq = self.Iq()
        iq['disco_items'].add_item('user@localhost')
        iq['disco_items'].add_item('user@localhost', node='foo')
        iq['disco_items'].add_item('test@localhost')

        iq['disco_items'].del_item('user@localhost', node='foo')

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#items">
              <item jid="user@localhost" />
              <item jid="test@localhost" />
            </query>
          </iq>
        """)

    def testGetItems(self):
        """Test retrieving items from disco#items stanza."""
        iq = self.Iq()
        iq['disco_items'].add_item('user@localhost')
        iq['disco_items'].add_item('user@localhost', node='foo')
        iq['disco_items'].add_item('test@localhost',
                                   node='bar',
                                   name='Tester')

        expected = set([('user@localhost', None, None),
                        ('user@localhost', 'foo', None),
                        ('test@localhost', 'bar', 'Tester')])
        self.failUnless(iq['disco_items']['items'] == expected,
                "Items do not match:\n%s\n%s" % (
                    expected,
                    iq['disco_items']['items']))

    def testRemoveAllItems(self):
        """Test removing all items from a disco#items stanza."""
        iq = self.Iq()
        iq['disco_items'].add_item('user@localhost')
        iq['disco_items'].add_item('user@localhost', node='foo')
        iq['disco_items'].add_item('test@localhost',
                                   node='bar',
                                   name='Tester')

        del iq['disco_items']['items']

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#items" />
          </iq>
        """)

    def testAddBatchItems(self):
        """Test adding multiple items to a disco#items stanza."""
        iq = self.Iq()
        items = [('user@localhost', 'foo', 'Test'),
                 ('test@localhost', None, None),
                 ('other@localhost', None, 'Other')]

        iq['disco_items']['items'] = items

        self.check(iq, """
          <iq>
            <query xmlns="http://jabber.org/protocol/disco#items">
              <item jid="user@localhost" node="foo" name="Test" />
              <item jid="test@localhost" />
              <item jid="other@localhost" name="Other" />
            </query>
          </iq>
        """)

suite = unittest.TestLoader().loadTestsFromTestCase(TestDisco)
