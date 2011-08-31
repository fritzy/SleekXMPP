import sys
import time
import threading

from sleekxmpp.test import *


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


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamPubsub)
