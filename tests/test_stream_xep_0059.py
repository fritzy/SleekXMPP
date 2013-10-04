import threading

import unittest
from sleekxmpp.test import SleekTest
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins.xep_0030 import DiscoItems
from sleekxmpp.plugins.xep_0059 import ResultIterator, Set


class TestStreamSet(SleekTest):

    def setUp(self):
        register_stanza_plugin(DiscoItems, Set)

    def tearDown(self):
        self.stream_close()

    def iter(self, rev=False):
        q = self.xmpp.Iq()
        q['type'] = 'get'
        it = ResultIterator(q, 'disco_items', amount='1', reverse=rev)
        for i in it:
            for j in i['disco_items']['items']:
                self.items.append(j[0])

    def testResultIterator(self):
        self.items = []
        self.stream_start(mode='client')
        t = threading.Thread(target=self.iter)
        t.start()
        self.send("""
          <iq type="get" id="2">
            <query xmlns="http://jabber.org/protocol/disco#items">
              <set xmlns="http://jabber.org/protocol/rsm">
                <max>1</max>
              </set>
            </query>
          </iq>
        """)
        self.recv("""
          <iq type="result" id="2">
            <query xmlns="http://jabber.org/protocol/disco#items">
              <item jid="item1" />
              <set xmlns="http://jabber.org/protocol/rsm">
                <last>item1</last>
              </set>
            </query>
          </iq>
        """)
        self.send("""
          <iq type="get" id="3">
            <query xmlns="http://jabber.org/protocol/disco#items">
              <set xmlns="http://jabber.org/protocol/rsm">
                <max>1</max>
                <after>item1</after>
              </set>
            </query>
          </iq>
        """)
        self.recv("""
          <iq type="result" id="3">
            <query xmlns="http://jabber.org/protocol/disco#items">
              <item jid="item2" />
              <set xmlns="http://jabber.org/protocol/rsm">
                <last>item2</last>
              </set>
            </query>
          </iq>
        """)
        self.send("""
          <iq type="get" id="4">
            <query xmlns="http://jabber.org/protocol/disco#items">
              <set xmlns="http://jabber.org/protocol/rsm">
                <max>1</max>
                <after>item2</after>
              </set>
            </query>
          </iq>
        """)
        self.recv("""
          <iq type="result" id="4">
            <query xmlns="http://jabber.org/protocol/disco#items">
              <item jid="item2" />
              <set xmlns="http://jabber.org/protocol/rsm">
              </set>
            </query>
          </iq>
        """)
        t.join()
        self.failUnless(self.items == ['item1', 'item2'])

    def testResultIteratorReverse(self):
        self.items = []
        self.stream_start(mode='client')

        t = threading.Thread(target=self.iter, args=(True,))
        t.start()

        self.send("""
          <iq type="get" id="2">
            <query xmlns="http://jabber.org/protocol/disco#items">
              <set xmlns="http://jabber.org/protocol/rsm">
                <max>1</max>
                <before />
              </set>
            </query>
          </iq>
        """)
        self.recv("""
          <iq type="result" id="2">
            <query xmlns="http://jabber.org/protocol/disco#items">
              <item jid="item2" />
              <set xmlns="http://jabber.org/protocol/rsm">
                <first>item2</first>
              </set>
            </query>
          </iq>
        """)
        self.send("""
          <iq type="get" id="3">
            <query xmlns="http://jabber.org/protocol/disco#items">
              <set xmlns="http://jabber.org/protocol/rsm">
                <max>1</max>
                <before>item2</before>
              </set>
            </query>
          </iq>
        """)
        self.recv("""
          <iq type="result" id="3">
            <query xmlns="http://jabber.org/protocol/disco#items">
              <item jid="item1" />
              <set xmlns="http://jabber.org/protocol/rsm">
                <first>item1</first>
              </set>
            </query>
          </iq>
        """)
        self.send("""
          <iq type="get" id="4">
            <query xmlns="http://jabber.org/protocol/disco#items">
              <set xmlns="http://jabber.org/protocol/rsm">
                <max>1</max>
                <before>item1</before>
              </set>
            </query>
          </iq>
        """)
        self.recv("""
          <iq type="result" id="4">
            <query xmlns="http://jabber.org/protocol/disco#items">
              <item jid="item1" />
              <set xmlns="http://jabber.org/protocol/rsm">
              </set>
            </query>
          </iq>
        """)

        t.join()
        self.failUnless(self.items == ['item2', 'item1'])


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamSet)
