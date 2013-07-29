import time
import unittest
from sleekxmpp.test import SleekTest


class TestStreamTester(SleekTest):
    """
    Test that we can simulate and test a stanza stream.
    """

    def tearDown(self):
        self.stream_close()

    def testClientEcho(self):
        """Test that we can interact with a ClientXMPP instance."""
        self.stream_start(mode='client')

        def echo(msg):
            msg.reply('Thanks for sending: %(body)s' % msg).send()

        self.xmpp.add_event_handler('message', echo)

        self.recv("""
          <message to="tester@localhost" from="user@localhost">
            <body>Hi!</body>
          </message>
        """)

        self.send("""
          <message to="user@localhost">
            <body>Thanks for sending: Hi!</body>
          </message>
        """)

    def testComponentEcho(self):
        """Test that we can interact with a ComponentXMPP instance."""
        self.stream_start(mode='component')

        def echo(msg):
            msg.reply('Thanks for sending: %(body)s' % msg).send()

        self.xmpp.add_event_handler('message', echo)

        self.recv("""
          <message to="tester.localhost" from="user@localhost">
            <body>Hi!</body>
          </message>
        """)

        self.send("""
          <message to="user@localhost" from="tester.localhost">
            <body>Thanks for sending: Hi!</body>
          </message>
        """)

    def testSendStreamHeader(self):
        """Test that we can check a sent stream header."""
        self.stream_start(mode='client', skip=False)
        self.send_header(sto='localhost')

    def testStreamDisconnect(self):
        """Test that the test socket can simulate disconnections."""
        self.stream_start()
        events = set()

        def stream_error(event):
            events.add('socket_error')

        self.xmpp.add_event_handler('socket_error', stream_error)

        self.stream_disconnect()
        self.xmpp.send_raw('  ')

        time.sleep(.1)

        self.failUnless('socket_error' in events,
                "Stream error event not raised: %s" % events)


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamTester)
