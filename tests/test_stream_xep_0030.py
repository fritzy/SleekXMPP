import time
from sleekxmpp.test import *


class TestStreamDisco(SleekTest):
    """
    Test using the XEP-0030 plugin.
    """

    def tearDown(self):
        self.stream_close()

    def testInfoEmptyNode(self):
        """
        Info queries to a node MUST have at least one identity
        and feature, namely http://jabber.org/protocol/disco#info.

        Since the XEP-0030 plugin is loaded, a disco response should
        be generated and not an error result.
        """
        self.stream_start(plugins=['xep_0030'])

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
          </iq>""")

    def testInfoEmptyNodeComponent(self):
        """
        Test requesting an empty node using a Component.
        """
        self.stream_start(mode='component',
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
          </iq>""")

    def testInfoIncludeNode(self):
        """
        Results for info queries directed to a particular node MUST
        include the node in the query response.
        """
        self.stream_start(plugins=['xep_0030'])

        self.xmpp['xep_0030'].add_node('testing')

        self.recv("""
          <iq type="get" id="test">
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


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamDisco)
