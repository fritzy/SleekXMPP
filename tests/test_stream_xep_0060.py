import threading

import unittest
from sleekxmpp.test import SleekTest
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
        self.xmpp['xep_0060'].create_node(
            'pubsub.example.com',
            'princely_musings',
            block=False)
        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <create node="princely_musings" />
            </pubsub>
          </iq>
        """)

    def testCreateNodeConfig(self):
        """Test creating a node with a config"""
        form = self.xmpp['xep_0004'].stanza.Form()
        form['type'] = 'submit'
        form.add_field(var='pubsub#access_model', value='whitelist')

        self.xmpp['xep_0060'].create_node(
                'pubsub.example.com',
                'princely_musings',
                config=form, block=False)

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

    def testDeleteNode(self):
        """Test deleting a node"""
        self.xmpp['xep_0060'].delete_node(
            'pubsub.example.com',
            'some_node',
            block=False)
        self.send("""
          <iq type="set" to="pubsub.example.com" id="1">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <delete node="some_node" />
            </pubsub>
          </iq>
        """)

    def testSubscribeCase1(self):
        """
        Test subscribing to a node: Case 1:
        No subscribee, default 'from' JID, bare JID
        """
        self.xmpp['xep_0060'].subscribe(
            'pubsub.example.com',
            'somenode',
            block=False)
        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <subscribe node="somenode" jid="tester@localhost" />
            </pubsub>
          </iq>
        """)

    def testSubscribeCase2(self):
        """
        Test subscribing to a node: Case 2:
        No subscribee, given 'from' JID, bare JID
        """
        self.xmpp['xep_0060'].subscribe(
            'pubsub.example.com',
            'somenode',
            ifrom='foo@comp.example.com/bar',
            block=False)
        self.send("""
          <iq type="set" id="1"
              to="pubsub.example.com" from="foo@comp.example.com/bar">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <subscribe node="somenode" jid="foo@comp.example.com" />
            </pubsub>
          </iq>
        """)

    def testSubscribeCase3(self):
        """
        Test subscribing to a node: Case 3:
        No subscribee, given 'from' JID, full JID
        """
        self.xmpp['xep_0060'].subscribe(
            'pubsub.example.com',
            'somenode',
            ifrom='foo@comp.example.com/bar',
            bare=False,
            block=False)
        self.send("""
          <iq type="set" id="1"
              to="pubsub.example.com" from="foo@comp.example.com/bar">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <subscribe node="somenode" jid="foo@comp.example.com/bar" />
            </pubsub>
          </iq>
        """)

    def testSubscribeCase4(self):
        """
        Test subscribing to a node: Case 4:
        No subscribee, no 'from' JID, full JID
        """
        self.stream_close()
        self.stream_start(jid='tester@localhost/full')

        self.xmpp['xep_0060'].subscribe(
            'pubsub.example.com',
            'somenode',
            bare=False,
            block=False)
        self.send("""
          <iq type="set" id="1"
              to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <subscribe node="somenode" jid="tester@localhost/full" />
            </pubsub>
          </iq>
        """)

    def testSubscribeCase5(self):
        """
        Test subscribing to a node: Case 5:
        Subscribee given
        """
        self.xmpp['xep_0060'].subscribe(
            'pubsub.example.com',
            'somenode',
            subscribee='user@example.com/foo',
            ifrom='foo@comp.example.com/bar',
            block=False)
        self.send("""
          <iq type="set" id="1"
              to="pubsub.example.com" from="foo@comp.example.com/bar">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <subscribe node="somenode" jid="user@example.com/foo" />
            </pubsub>
          </iq>
        """)

    def testSubscribeWithOptions(self):
        """Test subscribing to a node, with options."""
        opts = self.xmpp['xep_0004'].make_form()
        opts.add_field(
                var='FORM_TYPE',
                value='http://jabber.org/protocol/pubsub#subscribe_options',
                ftype='hidden')
        opts.add_field(
                var='pubsub#digest',
                value=False,
                ftype='boolean')
        opts['type'] = 'submit'

        self.xmpp['xep_0060'].subscribe(
            'pubsub.example.com',
            'somenode',
            options=opts,
            block=False)
        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <subscribe node="somenode" jid="tester@localhost" />
              <options>
                <x xmlns="jabber:x:data" type="submit">
                  <field var="FORM_TYPE">
                    <value>http://jabber.org/protocol/pubsub#subscribe_options</value>
                  </field>
                  <field var="pubsub#digest">
                    <value>0</value>
                  </field>
                </x>
              </options>
            </pubsub>
          </iq>
        """)

    def testUnsubscribeCase1(self):
        """
        Test unsubscribing from a node: Case 1:
        No subscribee, default 'from' JID, bare JID
        """
        self.xmpp['xep_0060'].unsubscribe(
            'pubsub.example.com',
            'somenode',
            block=False)
        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <unsubscribe node="somenode" jid="tester@localhost" />
            </pubsub>
          </iq>
        """)

    def testUnsubscribeCase2(self):
        """
        Test unsubscribing from a node: Case 2:
        No subscribee, given 'from' JID, bare JID
        """
        self.xmpp['xep_0060'].unsubscribe(
            'pubsub.example.com',
            'somenode',
            ifrom='foo@comp.example.com/bar',
            block=False)
        self.send("""
          <iq type="set" id="1"
              to="pubsub.example.com" from="foo@comp.example.com/bar">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <unsubscribe node="somenode" jid="foo@comp.example.com" />
            </pubsub>
          </iq>
        """)

    def testUnsubscribeCase3(self):
        """
        Test unsubscribing from a node: Case 3:
        No subscribee, given 'from' JID, full JID
        """
        self.xmpp['xep_0060'].unsubscribe(
            'pubsub.example.com',
            'somenode',
            ifrom='foo@comp.example.com/bar',
            bare=False,
            block=False)
        self.send("""
          <iq type="set" id="1"
              to="pubsub.example.com" from="foo@comp.example.com/bar">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <unsubscribe node="somenode" jid="foo@comp.example.com/bar" />
            </pubsub>
          </iq>
        """)

    def testUnsubscribeCase4(self):
        """
        Test unsubscribing from a node: Case 4:
        No subscribee, no 'from' JID, full JID
        """
        self.stream_close()
        self.stream_start(jid='tester@localhost/full')

        self.xmpp['xep_0060'].unsubscribe(
            'pubsub.example.com',
            'somenode',
            bare=False,
            block=False)
        self.send("""
          <iq type="set" id="1"
              to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <unsubscribe node="somenode" jid="tester@localhost/full" />
            </pubsub>
          </iq>
        """)

    def testUnsubscribeCase5(self):
        """
        Test unsubscribing from a node: Case 5:
        Subscribee given
        """
        self.xmpp['xep_0060'].unsubscribe(
            'pubsub.example.com',
            'somenode',
            subscribee='user@example.com/foo',
            ifrom='foo@comp.example.com/bar',
            block=False)
        self.send("""
          <iq type="set" id="1"
              to="pubsub.example.com" from="foo@comp.example.com/bar">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <unsubscribe node="somenode" jid="user@example.com/foo" />
            </pubsub>
          </iq>
        """)

    def testGetDefaultNodeConfig(self):
        """Test retrieving the default node config for a pubsub service."""
        self.xmpp['xep_0060'].get_node_config(
                'pubsub.example.com',
                block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <default />
            </pubsub>
          </iq>
        """, use_values=False)

    def testGetNodeConfig(self):
        """Test getting the config for a given node."""
        self.xmpp['xep_0060'].get_node_config(
            'pubsub.example.com',
            'somenode',
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <configure node="somenode" />
            </pubsub>
          </iq>
        """, use_values=False)

    def testSetNodeConfig(self):
        """Test setting the configuration for a node."""
        form = self.xmpp['xep_0004'].make_form()
        form.add_field(var='FORM_TYPE', ftype='hidden',
                       value='http://jabber.org/protocol/pubsub#node_config')
        form.add_field(var='pubsub#title', ftype='text-single',
                       value='This is awesome!')
        form['type'] = 'submit'

        self.xmpp['xep_0060'].set_node_config(
            'pubsub.example.com',
            'somenode',
            form,
            block=False)
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

    def testPublishNoItems(self):
        """Test publishing no items (in order to generate events)"""
        self.xmpp['xep_0060'].publish(
            'pubsub.example.com',
            'somenode',
            block=False)
        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <publish node="somenode" />
            </pubsub>
          </iq>
        """)

    def testPublishSingle(self):
        """Test publishing a single item."""
        payload = AtomEntry()
        payload['title'] = 'Test'

        register_stanza_plugin(self.xmpp['xep_0060'].stanza.Item, AtomEntry)

        self.xmpp['xep_0060'].publish(
            'pubsub.example.com',
            'somenode',
            id='id42',
            payload=payload,
            block=False)
        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <publish node="somenode">
                <item id="id42">
                  <entry xmlns="http://www.w3.org/2005/Atom">
                    <title>Test</title>
                  </entry>
                </item>
              </publish>
            </pubsub>
          </iq>
        """, use_values=False)

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

        self.xmpp['xep_0060'].publish(
            'pubsub.example.com',
            'somenode',
            id='ID42',
            payload=payload,
            options=options,
            block=False)
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

    def testRetract(self):
        """Test deleting an item."""
        self.xmpp['xep_0060'].retract(
            'pubsub.example.com',
            'somenode',
            'ID1',
            notify=True,
            block=False)
        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <retract node="somenode" notify="true">
                <item id="ID1" />
              </retract>
            </pubsub>
          </iq>
        """)

    def testRetract(self):
        """Test deleting an item."""
        self.xmpp['xep_0060'].retract(
            'pubsub.example.com',
            'somenode',
            'ID1',
            block=False)
        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <retract node="somenode">
                <item id="ID1" />
              </retract>
            </pubsub>
          </iq>
        """)

    def testPurge(self):
        """Test removing all items from a node."""
        self.xmpp['xep_0060'].purge(
                'pubsub.example.com',
                'somenode',
                block=False)
        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <purge node="somenode" />
            </pubsub>
          </iq>
        """)

    def testGetItem(self):
        """Test retrieving a single item."""
        self.xmpp['xep_0060'].get_item(
            'pubsub.example.com',
            'somenode',
            'id42',
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <items node="somenode">
                <item id="id42" />
              </items>
            </pubsub>
          </iq>
        """)

    def testGetLatestItems(self):
        """Test retrieving the most recent N items."""
        self.xmpp['xep_0060'].get_items(
            'pubsub.example.com',
            'somenode',
            max_items=3,
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <items node="somenode" max_items="3" />
            </pubsub>
          </iq>
        """)

    def testGetAllItems(self):
        """Test retrieving all items."""
        self.xmpp['xep_0060'].get_items(
            'pubsub.example.com',
            'somenode',
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <items node="somenode" />
            </pubsub>
          </iq>
        """)

    def testGetSpecificItems(self):
        """Test retrieving a specific set of items."""
        self.xmpp['xep_0060'].get_items(
            'pubsub.example.com',
            'somenode',
            item_ids=['A', 'B', 'C'],
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <items node="somenode">
                <item id="A" />
                <item id="B" />
                <item id="C" />
              </items>
            </pubsub>
          </iq>
        """)

    def testGetSubscriptionGlobalDefaultOptions(self):
        """Test getting the subscription options for a node/JID."""
        self.xmpp['xep_0060'].get_subscription_options(
            'pubsub.example.com',
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <default />
            </pubsub>
          </iq>
        """, use_values=False)

    def testGetSubscriptionNodeDefaultOptions(self):
        """Test getting the subscription options for a node/JID."""
        self.xmpp['xep_0060'].get_subscription_options(
            'pubsub.example.com',
            node='somenode',
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <default node="somenode" />
            </pubsub>
          </iq>
        """, use_values=False)

    def testGetSubscriptionOptions(self):
        """Test getting the subscription options for a node/JID."""
        self.xmpp['xep_0060'].get_subscription_options(
            'pubsub.example.com',
            'somenode',
            'tester@localhost',
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <options node="somenode" jid="tester@localhost" />
            </pubsub>
          </iq>
        """, use_values=False)

    def testSetSubscriptionOptions(self):
        """Test setting the subscription options for a node/JID."""
        opts = self.xmpp['xep_0004'].make_form()
        opts.add_field(
                var='FORM_TYPE',
                value='http://jabber.org/protocol/pubsub#subscribe_options',
                ftype='hidden')
        opts.add_field(
                var='pubsub#digest',
                value=False,
                ftype='boolean')
        opts['type'] = 'submit'

        self.xmpp['xep_0060'].set_subscription_options(
            'pubsub.example.com',
            'somenode',
            'tester@localhost',
            opts,
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <options node="somenode" jid="tester@localhost">
                <x xmlns="jabber:x:data" type="submit">
                  <field var="FORM_TYPE">
                    <value>http://jabber.org/protocol/pubsub#subscribe_options</value>
                  </field>
                  <field var="pubsub#digest">
                    <value>0</value>
                  </field>
                </x>
              </options>
            </pubsub>
          </iq>
        """)

    def testGetNodeSubscriptions(self):
        """Test retrieving all subscriptions for a node."""
        self.xmpp['xep_0060'].get_node_subscriptions(
            'pubsub.example.com',
            'somenode',
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <subscriptions node="somenode" />
            </pubsub>
          </iq>
        """)

    def testGetSubscriptions(self):
        """Test retrieving a users's subscriptions."""
        self.xmpp['xep_0060'].get_subscriptions(
            'pubsub.example.com',
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <subscriptions />
            </pubsub>
          </iq>
        """)

    def testGetSubscriptionsForNode(self):
        """Test retrieving a users's subscriptions for a given node."""
        self.xmpp['xep_0060'].get_subscriptions(
            'pubsub.example.com',
            node='somenode',
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <subscriptions node="somenode" />
            </pubsub>
          </iq>
        """)

    def testGetAffiliations(self):
        """Test retrieving a users's affiliations."""
        self.xmpp['xep_0060'].get_affiliations(
            'pubsub.example.com',
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <affiliations />
            </pubsub>
          </iq>
        """)

    def testGetAffiliatinssForNode(self):
        """Test retrieving a users's affiliations for a given node."""
        self.xmpp['xep_0060'].get_affiliations(
            'pubsub.example.com',
            node='somenode',
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <affiliations node="somenode" />
            </pubsub>
          </iq>
        """)

    def testGetNodeAffiliations(self):
        """Test getting the affiliations for a node."""
        self.xmpp['xep_0060'].get_node_affiliations(
            'pubsub.example.com',
            'somenode',
            block=False)
        self.send("""
          <iq type="get" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <affiliations node="somenode" />
            </pubsub>
          </iq>
        """)

    def testModifySubscriptions(self):
        """Test owner modifying node subscriptions."""
        self.xmpp['xep_0060'].modify_subscriptions(
            'pubsub.example.com',
            'somenode',
            subscriptions=[('user@example.com', 'subscribed'),
                           ('foo@example.net', 'none')],
            block=False)
        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <subscriptions node="somenode">
                <subscription jid="user@example.com" subscription="subscribed" />
                <subscription jid="foo@example.net" subscription="none" />
              </subscriptions>
            </pubsub>
          </iq>
        """)

    def testModifyAffiliations(self):
        """Test owner modifying node affiliations."""
        self.xmpp['xep_0060'].modify_affiliations(
            'pubsub.example.com',
            'somenode',
            affiliations=[('user@example.com', 'publisher'),
                          ('foo@example.net', 'none')],
            block=False)
        self.send("""
          <iq type="set" id="1" to="pubsub.example.com">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <affiliations node="somenode">
                <affiliation jid="user@example.com" affiliation="publisher" />
                <affiliation jid="foo@example.net" affiliation="none" />
              </affiliations>
            </pubsub>
          </iq>
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamPubsub)
