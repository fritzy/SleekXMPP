import time
import threading

import unittest
from sleekxmpp.test import SleekTest


class TestStreamDisco(SleekTest):

    """
    Test using the XEP-0030 plugin.
    """

    def tearDown(self):
        self.stream_close()

    def testInfoEmptyDefaultNode(self):
        """
        Info query result from an entity MUST have at least one identity
        and feature, namely http://jabber.org/protocol/disco#info.

        Since the XEP-0030 plugin is loaded, a disco response should
        be generated and not an error result.
        """
        self.stream_start(mode='client',
                          plugins=['xep_0030'])

        self.recv("""
          <iq type="get" id="test">
            <query xmlns="http://jabber.org/protocol/disco#info" />
          </iq>
        """)

        self.send("""
          <iq type="result" id="test">
            <query xmlns="http://jabber.org/protocol/disco#info">
              <identity category="client" type="bot" />
              <feature var="http://jabber.org/protocol/disco#info" />
            </query>
          </iq>
        """)

    def testInfoEmptyDefaultNodeComponent(self):
        """
        Test requesting an empty, default node using a Component.
        """
        self.stream_start(mode='component',
                          jid='tester.localhost',
                          plugins=['xep_0030'])

        self.recv("""
          <iq type="get" id="test">
            <query xmlns="http://jabber.org/protocol/disco#info" />
          </iq>
        """)

        self.send("""
          <iq type="result" id="test">
            <query xmlns="http://jabber.org/protocol/disco#info">
              <identity category="component" type="generic" />
              <feature var="http://jabber.org/protocol/disco#info" />
            </query>
          </iq>
        """)

    def testInfoIncludeNode(self):
        """
        Results for info queries directed to a particular node MUST
        include the node in the query response.
        """
        self.stream_start(mode='client',
                          plugins=['xep_0030'])


        self.xmpp['xep_0030'].static.add_node(node='testing')

        self.recv("""
          <iq to="tester@localhost" type="get" id="test">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="testing" />
          </iq>
        """)

        self.send("""
          <iq type="result" id="test">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="testing">
            </query>
          </iq>""",
          method='mask')

    def testItemsIncludeNode(self):
        """
        Results for items queries directed to a particular node MUST
        include the node in the query response.
        """
        self.stream_start(mode='client',
                          plugins=['xep_0030'])


        self.xmpp['xep_0030'].static.add_node(node='testing')

        self.recv("""
          <iq to="tester@localhost" type="get" id="test">
            <query xmlns="http://jabber.org/protocol/disco#items"
                   node="testing" />
          </iq>
        """)

        self.send("""
          <iq type="result" id="test">
            <query xmlns="http://jabber.org/protocol/disco#items"
                   node="testing">
            </query>
          </iq>""",
          method='mask')

    def testDynamicInfoJID(self):
        """
        Test using a dynamic info handler for a particular JID.
        """
        self.stream_start(mode='client',
                          plugins=['xep_0030'])

        def dynamic_jid(jid, node, ifrom, iq):
            result = self.xmpp['xep_0030'].stanza.DiscoInfo()
            result['node'] = node
            result.add_identity('client', 'console', name='Dynamic Info')
            return result

        self.xmpp['xep_0030'].set_node_handler('get_info',
                                               jid='tester@localhost',
                                               handler=dynamic_jid)

        self.recv("""
          <iq type="get" id="test" to="tester@localhost">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="testing" />
          </iq>
        """)

        self.send("""
          <iq type="result" id="test">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="testing">
              <identity category="client"
                        type="console"
                        name="Dynamic Info" />
            </query>
          </iq>
        """)

    def testDynamicInfoGlobal(self):
        """
        Test using a dynamic info handler for all requests.
        """
        self.stream_start(mode='component',
                          jid='tester.localhost',
                          plugins=['xep_0030'])

        def dynamic_global(jid, node, ifrom, iq):
            result = self.xmpp['xep_0030'].stanza.DiscoInfo()
            result['node'] = node
            result.add_identity('component', 'generic', name='Dynamic Info')
            return result

        self.xmpp['xep_0030'].set_node_handler('get_info',
                                               handler=dynamic_global)

        self.recv("""
          <iq type="get" id="test"
              to="user@tester.localhost"
              from="tester@localhost">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="testing" />
          </iq>
        """)

        self.send("""
          <iq type="result" id="test"
              to="tester@localhost"
              from="user@tester.localhost">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="testing">
              <identity category="component"
                        type="generic"
                        name="Dynamic Info" />
            </query>
          </iq>
        """)

    def testOverrideJIDInfoHandler(self):
        """Test overriding a JID info handler."""
        self.stream_start(mode='client',
                          plugins=['xep_0030'])

        def dynamic_jid(jid, node, ifrom, iq):
            result = self.xmpp['xep_0030'].stanza.DiscoInfo()
            result['node'] = node
            result.add_identity('client', 'console', name='Dynamic Info')
            return result

        self.xmpp['xep_0030'].set_node_handler('get_info',
                                               jid='tester@localhost',
                                               handler=dynamic_jid)


        self.xmpp['xep_0030'].make_static(jid='tester@localhost',
                                          node='testing')

        self.xmpp['xep_0030'].add_identity(jid='tester@localhost',
                                           node='testing',
                                           category='automation',
                                           itype='command-list')

        self.recv("""
          <iq type="get" id="test" to="tester@localhost">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="testing" />
          </iq>
        """)

        self.send("""
          <iq type="result" id="test">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="testing">
              <identity category="automation"
                        type="command-list" />
            </query>
          </iq>
        """)

    def testOverrideGlobalInfoHandler(self):
        """Test overriding the global JID info handler."""
        self.stream_start(mode='component',
                          jid='tester.localhost',
                          plugins=['xep_0030'])

        def dynamic_global(jid, node, ifrom, iq):
            result = self.xmpp['xep_0030'].stanza.DiscoInfo()
            result['node'] = node
            result.add_identity('component', 'generic', name='Dynamic Info')
            return result

        self.xmpp['xep_0030'].set_node_handler('get_info',
                                               handler=dynamic_global)

        self.xmpp['xep_0030'].make_static(jid='user@tester.localhost',
                                          node='testing')

        self.xmpp['xep_0030'].add_feature(jid='user@tester.localhost',
                                          node='testing',
                                          feature='urn:xmpp:ping')

        self.recv("""
          <iq type="get" id="test"
              to="user@tester.localhost"
              from="tester@localhost">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="testing" />
          </iq>
        """)

        self.send("""
          <iq type="result" id="test"
              to="tester@localhost"
              from="user@tester.localhost">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="testing">
              <feature var="urn:xmpp:ping" />
            </query>
          </iq>
        """)

    def testGetInfoRemote(self):
        """
        Test sending a disco#info query to another entity
        and receiving the result.
        """
        self.stream_start(mode='client',
                          plugins=['xep_0030'])

        events = set()

        def handle_disco_info(iq):
            events.add('disco_info')


        self.xmpp.add_event_handler('disco_info', handle_disco_info)

        t = threading.Thread(name="get_info",
                             target=self.xmpp['xep_0030'].get_info,
                             args=('user@localhost', 'foo'))
        t.start()

        self.send("""
          <iq type="get" to="user@localhost" id="1">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="foo" />
          </iq>
        """)

        self.recv("""
          <iq type="result" to="tester@localhost" id="1">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="foo">
              <identity category="client" type="bot" />
              <feature var="urn:xmpp:ping" />
            </query>
          </iq>
        """)

        # Wait for disco#info request to be received.
        t.join()

        time.sleep(0.1)

        self.assertEqual(events, set(('disco_info',)),
                "Disco info event was not triggered: %s" % events)

    def testDynamicItemsJID(self):
        """
        Test using a dynamic items handler for a particular JID.
        """
        self.stream_start(mode='client',
                          plugins=['xep_0030'])

        def dynamic_jid(jid, node, ifrom, iq):
            result = self.xmpp['xep_0030'].stanza.DiscoItems()
            result['node'] = node
            result.add_item('tester@localhost', node='foo', name='JID')
            return result

        self.xmpp['xep_0030'].set_node_handler('get_items',
                                               jid='tester@localhost',
                                               handler=dynamic_jid)

        self.recv("""
          <iq type="get" id="test" to="tester@localhost">
            <query xmlns="http://jabber.org/protocol/disco#items"
                   node="testing" />
          </iq>
        """)

        self.send("""
          <iq type="result" id="test">
            <query xmlns="http://jabber.org/protocol/disco#items"
                   node="testing">
              <item jid="tester@localhost" node="foo" name="JID" />
            </query>
          </iq>
        """)

    def testDynamicItemsGlobal(self):
        """
        Test using a dynamic items handler for all requests.
        """
        self.stream_start(mode='component',
                          jid='tester.localhost',
                          plugins=['xep_0030'])

        def dynamic_global(jid, node, ifrom, iq):
            result = self.xmpp['xep_0030'].stanza.DiscoItems()
            result['node'] = node
            result.add_item('tester@localhost', node='foo', name='Global')
            return result

        self.xmpp['xep_0030'].set_node_handler('get_items',
                                               handler=dynamic_global)

        self.recv("""
          <iq type="get" id="test"
              to="user@tester.localhost"
              from="tester@localhost">
            <query xmlns="http://jabber.org/protocol/disco#items"
                   node="testing" />
          </iq>
        """)

        self.send("""
          <iq type="result" id="test"
              to="tester@localhost"
              from="user@tester.localhost">
            <query xmlns="http://jabber.org/protocol/disco#items"
                   node="testing">
              <item jid="tester@localhost" node="foo" name="Global" />
            </query>
          </iq>
        """)

    def testOverrideJIDItemsHandler(self):
        """Test overriding a JID items handler."""
        self.stream_start(mode='client',
                          plugins=['xep_0030'])

        def dynamic_jid(jid, node, ifrom, iq):
            result = self.xmpp['xep_0030'].stanza.DiscoItems()
            result['node'] = node
            result.add_item('tester@localhost', node='foo', name='Global')
            return result

        self.xmpp['xep_0030'].set_node_handler('get_items',
                                               jid='tester@localhost',
                                               handler=dynamic_jid)


        self.xmpp['xep_0030'].make_static(jid='tester@localhost',
                                          node='testing')

        self.xmpp['xep_0030'].add_item(ijid='tester@localhost',
                                       node='testing',
                                       jid='tester@localhost',
                                       subnode='foo',
                                       name='Test')

        self.recv("""
          <iq type="get" id="test" to="tester@localhost">
            <query xmlns="http://jabber.org/protocol/disco#items"
                   node="testing" />
          </iq>
        """)

        self.send("""
          <iq type="result" id="test">
            <query xmlns="http://jabber.org/protocol/disco#items"
                   node="testing">
              <item jid="tester@localhost" node="foo" name="Test" />
            </query>
          </iq>
        """)

    def testOverrideGlobalItemsHandler(self):
        """Test overriding the global JID items handler."""
        self.stream_start(mode='component',
                          jid='tester.localhost',
                          plugins=['xep_0030'])

        def dynamic_global(jid, node, ifrom, iq):
            result = self.xmpp['xep_0030'].stanza.DiscoItems()
            result['node'] = node
            result.add_item('tester.localhost', node='foo', name='Global')
            return result

        self.xmpp['xep_0030'].set_node_handler('get_items',
                                               handler=dynamic_global)

        self.xmpp['xep_0030'].make_static(jid='user@tester.localhost',
                                          node='testing')

        self.xmpp['xep_0030'].add_item(ijid='user@tester.localhost',
                                       node='testing',
                                       jid='user@tester.localhost',
                                       subnode='foo',
                                       name='Test')

        self.recv("""
          <iq type="get" id="test"
              to="user@tester.localhost"
              from="tester@localhost">
            <query xmlns="http://jabber.org/protocol/disco#items"
                   node="testing" />
          </iq>
        """)

        self.send("""
          <iq type="result" id="test"
              to="tester@localhost"
              from="user@tester.localhost">
            <query xmlns="http://jabber.org/protocol/disco#items"
                   node="testing">
              <item jid="user@tester.localhost" node="foo" name="Test" />
            </query>
          </iq>
        """)

    def testGetItemsRemote(self):
        """
        Test sending a disco#items query to another entity
        and receiving the result.
        """
        self.stream_start(mode='client',
                          plugins=['xep_0030'])

        events = set()
        results = set()

        def handle_disco_items(iq):
            events.add('disco_items')
            results.update(iq['disco_items']['items'])


        self.xmpp.add_event_handler('disco_items', handle_disco_items)

        t = threading.Thread(name="get_items",
                             target=self.xmpp['xep_0030'].get_items,
                             args=('user@localhost', 'foo'))
        t.start()

        self.send("""
          <iq type="get" to="user@localhost" id="1">
            <query xmlns="http://jabber.org/protocol/disco#items"
                   node="foo" />
          </iq>
        """)

        self.recv("""
          <iq type="result" to="tester@localhost" id="1">
            <query xmlns="http://jabber.org/protocol/disco#items"
                   node="foo">
              <item jid="user@localhost" node="bar" name="Test" />
              <item jid="user@localhost" node="baz" name="Test 2" />
            </query>
          </iq>
        """)

        # Wait for disco#items request to be received.
        t.join()

        time.sleep(0.1)

        items = set([('user@localhost', 'bar', 'Test'),
                     ('user@localhost', 'baz', 'Test 2')])
        self.assertEqual(events, set(('disco_items',)),
                "Disco items event was not triggered: %s" % events)
        self.assertEqual(results, items,
                "Unexpected items: %s" % results)

    def testGetItemsIterator(self):
        """Test interaction between XEP-0030 and XEP-0059 plugins."""

        raised_exceptions = []

        self.stream_start(mode='client',
                          plugins=['xep_0030', 'xep_0059'])

        results = self.xmpp['xep_0030'].get_items(jid='foo@localhost',
                                                  node='bar',
                                                  iterator=True)
        results.amount = 10

        def run_test():
            try:
                results.next()
            except StopIteration:
                raised_exceptions.append(True)

        t = threading.Thread(name="get_items_iterator",
                             target=run_test)
        t.start()

        self.send("""
          <iq id="2" type="get" to="foo@localhost">
            <query xmlns="http://jabber.org/protocol/disco#items"
                   node="bar">
              <set xmlns="http://jabber.org/protocol/rsm">
                <max>10</max>
              </set>
            </query>
          </iq>
        """)
        self.recv("""
          <iq id="2" type="result" to="tester@localhost">
            <query xmlns="http://jabber.org/protocol/disco#items">
              <set xmlns="http://jabber.org/protocol/rsm">
              </set>
            </query>
          </iq>
        """)

        t.join()

        self.assertEqual(raised_exceptions, [True],
             "StopIteration was not raised: %s" % raised_exceptions)


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamDisco)
