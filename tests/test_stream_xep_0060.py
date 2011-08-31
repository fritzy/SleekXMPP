import sys
import time
import threading

from sleekxmpp.test import *
from sleekxmpp.stanza.atom import AtomEntry
from sleekxmpp.xmlstream import register_stanza_plugin


class TestStreamPubsub(SleekTest):

    """
    Test using the XEP-0030 plugin.
    """

    def setUp(self):
        self.stream_start()

    def tearDown(self):
        self.stream_close()

    def testCreateInstantNode(self):
        """Test creating an instant node"""
        t = threading.Thread(name='create_node',
                             target=self.xmpp['xep_0060'].create_node,
                             args=('pubsub.example.com', None))
        t.start()

        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <create />
            </pubsub>
          </iq>
        """)

        self.recv("""
          <iq type="result" id="1"
              to="tester@localhost" from="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <create node="25e3d37dabbab9541f7523321421edc5bfeb2dae" />
            </pubsub>
          </iq>
        """)

        t.join()

    def testCreateNodeNoConfig(self):
        """Test creating a node without a config"""
        t = threading.Thread(name='create_node',
                             target=self.xmpp['xep_0060'].create_node,
                             args=('pubsub.example.com', 'princely_musings'))
        t.start()

        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <create node="princely_musings" />
            </pubsub>
          </iq>
        """)

        self.recv("""
          <iq type="result" id="1"
              to="tester@localhost" from="pubsub.example.com" />
        """)

        t.join()

    def testCreateNodeConfig(self):
        """Test creating a node with a config"""
        form = self.xmpp['xep_0004'].stanza.Form()
        form['type'] = 'submit'
        form.add_field(var='pubsub#access_model', value='whitelist')

        t = threading.Thread(name='create_node',
                             target=self.xmpp['xep_0060'].create_node,
                             args=('pubsub.example.com', 'princely_musings'),
                             kwargs={'config': form})
        t.start()

        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <create node="princely_musings" />
              <configure>
                <x xmlns="jabber:x:data" type="submit">
                  <field var="pubsub#access_model">
                    <value>whitelist</value>
                  </field>
                  <field var="FORM_TYPE">
                    <value>http://jabber.org/protocol/pubsub#node_config</value>
                  </field>
                </x>
              </configure>
            </pubsub>
          </iq>
        """)

        self.recv("""
          <iq type="result" id="1"
              to="tester@localhost" from="pubsub.example.com" />
        """)

        t.join()

    def testDeleteNode(self):
        """Test deleting a node"""
        t = threading.Thread(name='delete_node',
                             target=self.xmpp['xep_0060'].delete_node,
                             args=('pubsub.example.com', 'some_node'))
        t.start()

        self.send("""
          <iq type="set" to="pubsub.example.com" id="1">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <delete node="some_node" />
            </pubsub>
          </iq>
        """)

        self.recv("""
          <iq type="result" id="1"
              to="tester@localhost" from="pubsub.example.com" />
        """)

        t.join()

    def testSubscribe(self):
        """Test subscribing to a node"""

        def run_test(jid, bare, ifrom, send, recv):
            t = threading.Thread(name='subscribe',
                                 target=self.xmpp['xep_0060'].subscribe,
                                 args=('pubsub.example.com', 'some_node'),
                                 kwargs={'subscribee': jid,
                                         'bare': bare,
                                         'ifrom': ifrom})
            t.start()
            self.send(send)
            self.recv(recv)
            t.join()

        # Case 1: No subscribee, default 'from' JID, bare JID
        run_test(None, True, None,
            """
              <iq type="set" id="1" to="pubsub.example.com">
                <pubsub xmlns="http://jabber.org/protocol/pubsub">
                  <subscribe node="some_node" jid="tester@localhost" />
                </pubsub>
              </iq>
            """,
            """
              <iq type="result" id="1"
                  to="tester@localhost" from="pubsub.example.com" />
            """)

        # Case 2: No subscribee, given 'from' JID, bare JID
        run_test(None, True, 'foo@comp.example.com/bar',
            """
              <iq type="set" id="2"
                  to="pubsub.example.com" from="foo@comp.example.com/bar">
                <pubsub xmlns="http://jabber.org/protocol/pubsub">
                  <subscribe node="some_node" jid="foo@comp.example.com" />
                </pubsub>
              </iq>
            """,
            """
              <iq type="result" id="2"
                  to="foo@comp.example.com/bar" from="pubsub.example.com" />
            """)

        # Case 3: No subscribee, given 'from' JID, full JID
        run_test(None, False, 'foo@comp.example.com/bar',
            """
              <iq type="set" id="3"
                  to="pubsub.example.com" from="foo@comp.example.com/bar">
                <pubsub xmlns="http://jabber.org/protocol/pubsub">
                  <subscribe node="some_node" jid="foo@comp.example.com/bar" />
                </pubsub>
              </iq>
            """,
            """
              <iq type="result" id="3"
                  to="foo@comp.example.com/bar" from="pubsub.example.com" />
            """)

        # Case 4: Subscribee
        run_test('user@example.com/foo', True, 'foo@comp.example.com/bar',
            """
              <iq type="set" id="4"
                  to="pubsub.example.com" from="foo@comp.example.com/bar">
                <pubsub xmlns="http://jabber.org/protocol/pubsub">
                  <subscribe node="some_node" jid="user@example.com/foo" />
                </pubsub>
              </iq>
            """,
            """
              <iq type="result" id="4"
                  to="foo@comp.example.com/bar" from="pubsub.example.com" />
            """)

    def testSubscribeWithOptions(self):
        pass

    def testUnubscribe(self):
        """Test unsubscribing from a node"""

        def run_test(jid, bare, ifrom, send, recv):
            t = threading.Thread(name='unsubscribe',
                                 target=self.xmpp['xep_0060'].unsubscribe,
                                 args=('pubsub.example.com', 'some_node'),
                                 kwargs={'subscribee': jid,
                                         'bare': bare,
                                         'ifrom': ifrom})
            t.start()
            self.send(send)
            self.recv(recv)
            t.join()

        # Case 1: No subscribee, default 'from' JID, bare JID
        run_test(None, True, None,
            """
              <iq type="set" id="1" to="pubsub.example.com">
                <pubsub xmlns="http://jabber.org/protocol/pubsub">
                  <unsubscribe node="some_node" jid="tester@localhost" />
                </pubsub>
              </iq>
            """,
            """
              <iq type="result" id="1"
                  to="tester@localhost" from="pubsub.example.com" />
            """)

        # Case 2: No subscribee, given 'from' JID, bare JID
        run_test(None, True, 'foo@comp.example.com/bar',
            """
              <iq type="set" id="2"
                  to="pubsub.example.com" from="foo@comp.example.com/bar">
                <pubsub xmlns="http://jabber.org/protocol/pubsub">
                  <unsubscribe node="some_node" jid="foo@comp.example.com" />
                </pubsub>
              </iq>
            """,
            """
              <iq type="result" id="2"
                  to="foo@comp.example.com/bar" from="pubsub.example.com" />
            """)

        # Case 3: No subscribee, given 'from' JID, full JID
        run_test(None, False, 'foo@comp.example.com/bar',
            """
              <iq type="set" id="3"
                  to="pubsub.example.com" from="foo@comp.example.com/bar">
                <pubsub xmlns="http://jabber.org/protocol/pubsub">
                  <unsubscribe node="some_node" jid="foo@comp.example.com/bar" />
                </pubsub>
              </iq>
            """,
            """
              <iq type="result" id="3"
                  to="foo@comp.example.com/bar" from="pubsub.example.com" />
            """)

        # Case 4: Subscribee
        run_test('user@example.com/foo', True, 'foo@comp.example.com/bar',
            """
              <iq type="set" id="4"
                  to="pubsub.example.com" from="foo@comp.example.com/bar">
                <pubsub xmlns="http://jabber.org/protocol/pubsub">
                  <unsubscribe node="some_node" jid="user@example.com/foo" />
                </pubsub>
              </iq>
            """,
            """
              <iq type="result" id="4"
                  to="foo@comp.example.com/bar" from="pubsub.example.com" />
            """)

    def testGetDefaultConfig(self):
        """Test retrieving the default node configuration."""
        t = threading.Thread(name='default_config',
                             target=self.xmpp['xep_0060'].get_node_config,
                             args=('pubsub.example.com',))
        t.start()

        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <default />
            </pubsub>
          </iq>
        """, use_values=False)

        self.recv("""
          <iq type="result" id="1"
              to="tester@localhost" from="pubsub.example.com" />
        """)

        t.join()

    def testGetDefaultNodeConfig(self):
        """Test retrieving the default node config for a pubsub service."""
        t = threading.Thread(name='default_config',
                             target=self.xmpp['xep_0060'].get_node_config,
                             args=('pubsub.example.com', None))
        t.start()

        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <default />
            </pubsub>
          </iq>
        """, use_values=False)

        self.recv("""
          <iq type="result" id="1"
              to="tester@localhost" from="pubsub.example.com" />
        """)

        t.join()

    def testGetNodeConfig(self):
        """Test getting the config for a given node."""
        t = threading.Thread(name='node_config',
                             target=self.xmpp['xep_0060'].get_node_config,
                             args=('pubsub.example.com', 'somenode'))
        t.start()

        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <configure node="somenode" />
            </pubsub>
          </iq>
        """, use_values=False)

        self.recv("""
          <iq type="result" id="1"
              to="tester@localhost" from="pubsub.example.com" />
        """)

        t.join()

    def testSetNodeConfig(self):
        """Test setting the configuration for a node."""
        form = self.xmpp['xep_0004'].make_form()
        form.add_field(var='FORM_TYPE', ftype='hidden',
                       value='http://jabber.org/protocol/pubsub#node_config')
        form.add_field(var='pubsub#title', ftype='text-single',
                       value='This is awesome!')
        form['type'] = 'submit'

        t = threading.Thread(name='set_config',
                             target=self.xmpp['xep_0060'].set_node_config,
                             args=('pubsub.example.com', 'somenode', form))
        t.start()

        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <configure node="somenode">
                <x xmlns="jabber:x:data" type="submit">
                  <field var="FORM_TYPE">
                    <value>http://jabber.org/protocol/pubsub#node_config</value>
                  </field>
                  <field var="pubsub#title">
                    <value>This is awesome!</value>
                  </field>
                </x>
              </configure>
            </pubsub>
          </iq>
        """)

        self.recv("""
          <iq type="result" id="1"
              to="tester@localhost" from="pubsub.example.com" />
        """)

        t.join()

    def testPublishSingle(self):
        """Test publishing a single item."""
        payload = AtomEntry()
        payload['title'] = 'Test'

        register_stanza_plugin(self.xmpp['xep_0060'].stanza.Item, AtomEntry)

        t = threading.Thread(name='publish_single',
                             target=self.xmpp['xep_0060'].publish,
                             args=('pubsub.example.com', 'somenode'),
                             kwargs={'item_id': 'ID42',
                                     'payload': payload})
        t.start()

        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <publish node="somenode">
                <item id="ID42">
                  <entry xmlns="http://www.w3.org/2005/Atom">
                    <title>Test</title>
                  </entry>
                </item>
              </publish>
            </pubsub>
          </iq>
        """)

        self.recv("""
          <iq type="result" id="1"
              to="tester@localhost" from="pubsub.example.com" />
        """)

        t.join()

    def testPublishSingleOptions(self):
        """Test publishing a single item, with options."""
        payload = AtomEntry()
        payload['title'] = 'Test'

        register_stanza_plugin(self.xmpp['xep_0060'].stanza.Item, AtomEntry)

        options = self.xmpp['xep_0004'].make_form()
        options.add_field(var='FORM_TYPE', ftype='hidden',
              value='http://jabber.org/protocol/pubsub#publish-options')
        options.add_field(var='pubsub#access_model', ftype='text-single',
              value='presence')
        options['type'] = 'submit'

        t = threading.Thread(name='publish_single',
                             target=self.xmpp['xep_0060'].publish,
                             args=('pubsub.example.com', 'somenode'),
                             kwargs={'item_id': 'ID42',
                                     'payload': payload,
                                     'options': options})
        t.start()

        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <publish node="somenode">
                <item id="ID42">
                  <entry xmlns="http://www.w3.org/2005/Atom">
                    <title>Test</title>
                  </entry>
                </item>
              </publish>
              <publish-options>
                <x xmlns="jabber:x:data" type="submit">
                  <field var="FORM_TYPE">
                    <value>http://jabber.org/protocol/pubsub#publish-options</value>
                  </field>
                  <field var="pubsub#access_model">
                    <value>presence</value>
                  </field>
                </x>
              </publish-options>
            </pubsub>
          </iq>
        """, use_values=False)

        self.recv("""
          <iq type="result" id="1"
              to="tester@localhost" from="pubsub.example.com" />
        """)

        t.join()

    def testPublishMulti(self):
        """Test publishing multiple items."""
        pass

    def testPublishMultiOptions(self):
        """Test publishing multiple items, with options."""
        pass

    def testRetract(self):
        """Test deleting an item."""
        pass

    def testPurge(self):
        """Test removing all items from a node."""
        pass

    def testGetItem(self):
        """Test retrieving a single item."""
        pass

    def testGetLatestItems(self):
        """Test retrieving the most recent N items."""
        pass

    def testGetAllItems(self):
        """Test retrieving all items."""
        pass

    def testGetSpecificItems(self):
        """Test retrieving a specific set of items."""
        pass


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamPubsub)
