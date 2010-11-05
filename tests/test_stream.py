from sleekxmpp.test import *
import sleekxmpp.plugins.xep_0033 as xep_0033


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

suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamTester)
