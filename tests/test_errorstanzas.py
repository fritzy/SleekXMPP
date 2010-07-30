from sleektest import *

class TestErrorStanzas(SleekTest):
    
    def testSetup(self):
        """Test setting initial values in error stanza."""
        msg = self.Message()
        msg.enable('error')
        self.checkMessage(msg, """
          <message type="error">
            <error type="cancel">
              <feature-not-implemented xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
            </error>
          </message>
        """)

    def testCondition(self):
        """Test modifying the error condition."""
	msg = self.Message()
        msg['error']['condition'] = 'item-not-found'

        self.checkMessage(msg, """
          <message type="error">
            <error type="cancel">
              <item-not-found xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
            </error>
          </message>
        """)

        self.failUnless(msg['error']['condition'] == 'item-not-found', "Error condition doesn't match.")

        del msg['error']['condition']

        self.checkMessage(msg, """
          <message type="error">
            <error type="cancel" />
          </message>
         """)

    def testDelCondition(self):
        """Test that deleting error conditions doesn't remove extra elements."""
        msg = self.Message()
        msg['error']['text'] = 'Error!'
        msg['error']['condition'] = 'internal-server-error'
         
        del msg['error']['condition']

        self.checkMessage(msg, """
          <message type="error">
            <error type="cancel">
              <text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">Error!</text>
            </error>
          </message>
        """)

suite = unittest.TestLoader().loadTestsFromTestCase(TestErrorStanzas)
