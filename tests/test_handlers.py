from . sleektest import *
import sleekxmpp
from sleekxmpp.xmlstream.handler import *
from sleekxmpp.xmlstream.matcher import *

class TestHandlers(SleekTest):
    """
    Test that we can simulate and test a stanza stream.
    """

    def setUp(self):
        self.streamStart()

    def tearDown(self):
        self.streamClose()

    def testCallback(self):
        """Test using stream callback handlers."""

        def callback_handler(stanza):
            self.xmpp.sendRaw("""
              <message>
                <body>Success!</body>
              </message>
            """)

        callback = Callback('Test Callback',
                            MatchXPath('{test}tester'),
                            callback_handler)

        self.xmpp.registerHandler(callback)

        self.streamRecv("""<tester xmlns="test" />""")

        msg = self.Message()
        msg['body'] = 'Success!'
        self.streamSendMessage(msg)

    def testWaiter(self):
        """Test using stream waiter handler."""

        def waiter_handler(stanza):
            iq = self.xmpp.Iq()
            iq['id'] = 'test'
            iq['type'] = 'set'
            iq['query'] = 'test'
            reply = iq.send(block=True)
            if reply:
                self.xmpp.sendRaw("""
                  <message>
                    <body>Successful: %s</body>
                  </message>
                """ % reply['query'])

        self.xmpp.add_event_handler('message', waiter_handler, threaded=True)

        # Send message to trigger waiter_handler
        self.streamRecv("""
          <message>
            <body>Testing</body>
          </message>
        """)

        # Check that Iq was sent by waiter_handler
        iq = self.Iq()
        iq['id'] = 'test'
        iq['type'] = 'set'
        iq['query'] = 'test'
        self.streamSendIq(iq)

        # Send the reply Iq
        self.streamRecv("""
          <iq id="test" type="result">
            <query xmlns="test" />
          </iq>
        """)

        # Check that waiter_handler received the reply
        msg = self.Message()
        msg['body'] = 'Successful: test'
        self.streamSendMessage(msg)

    def testWaiterTimeout(self):
        """Test that waiter handler is removed after timeout."""

        def waiter_handler(stanza):
            iq = self.xmpp.Iq()
            iq['id'] = 'test2'
            iq['type'] = 'set'
            iq['query'] = 'test2'
            reply = iq.send(block=True, timeout=0)

        self.xmpp.add_event_handler('message', waiter_handler, threaded=True)

        # Start test by triggerig waiter_handler
        self.streamRecv("""<message><body>Start Test</body></message>""")

        # Check that Iq was sent to trigger start of timeout period
        iq = self.Iq()
        iq['id'] = 'test2'
        iq['type'] = 'set'
        iq['query'] = 'test2'
        self.streamSendIq(iq)

        # Check that the waiter is no longer registered
        waiter_exists = self.xmpp.removeHandler('IqWait_test2')

        self.failUnless(waiter_exists == False,
            "Waiter handler was not removed.")


suite = unittest.TestLoader().loadTestsFromTestCase(TestHandlers)
