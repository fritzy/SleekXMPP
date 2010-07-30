from sleektest import *
from sleekxmpp.xmlstream.stanzabase import ET


class TestIqStanzas(SleekTest):

    def setUp(self):
        """Start XML stream for testing."""
        self.streamStart()

    def tearDown(self):
        """Shutdown the XML stream after testing."""
        self.streamClose()

    def testSetup(self):
        """Test initializing default Iq values."""
        iq = self.Iq()
        self.checkIq(iq, """
          <iq id="0" />
        """)
    
    def testPayload(self):
        """Test setting Iq stanza payload."""
        iq = self.Iq()
        iq.setPayload(ET.Element('{test}tester'))
        self.checkIq(iq, """
          <iq id="0">
            <tester xmlns="test" />
          </iq>
        """, use_values=False)


    def testUnhandled(self):
        """Test behavior for Iq.unhandled."""
        self.streamRecv("""
          <iq id="test" type="get">
            <query xmlns="test" />
           </iq>
        """)

	iq = self.Iq()
        iq['id'] = 'test'
	iq['error']['condition'] = 'feature-not-implemented'
	iq['error']['text'] = 'No handlers registered for this request.'

        self.streamSendIq(iq, """
          <iq id="test" type="error">
            <error type="cancel">
              <feature-not-implemented xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
              <text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">
                No handlers registered for this request.
              </text>
            </error>
          </iq>
        """)

    def testQuery(self):
        """Test modifying query element of Iq stanzas."""
        iq = self.Iq()

        iq['query'] = 'query_ns'
        self.checkIq(iq, """
          <iq id="0">
            <query xmlns="query_ns" />
          </iq>
        """)

        iq['query'] = 'query_ns2'
        self.checkIq(iq, """
          <iq id="0">
            <query xmlns="query_ns2" />
          </iq>
        """)

	self.failUnless(iq['query'] == 'query_ns2', "Query namespace doesn't match")

	del iq['query']
	self.checkIq(iq, """
          <iq id="0" />
        """)

    def testReply(self):
        """Test setting proper result type in Iq replies."""
        iq = self.Iq()
	iq['to'] = 'user@localhost'
	iq['type'] = 'get'
        iq.reply()

	self.checkIq(iq, """
          <iq id="0" type="result" />
        """)

suite = unittest.TestLoader().loadTestsFromTestCase(TestIqStanzas)
