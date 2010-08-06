from . sleektest import *
import sleekxmpp.plugins.xep_0033 as xep_0033


class TestStreamTester(SleekTest):
    """
    Test that we can simulate and test a stanza stream.
    """

    def setUp(self):
        self.streamStart()

    def tearDown(self):
        self.streamClose()

    def testEcho(self):
        def echo(msg):
            msg.reply('Thanks for sending: %(body)s' % msg).send()
        
        self.xmpp.add_event_handler('message', echo)
        
        self.streamRecv("""
          <message to="tester@localhost" from="user@localhost">
            <body>Hi!</body>
          </message>
        """)
        
        self.streamSendMessage("""
          <message to="user@localhost">
            <body>Thanks for sending: Hi!</body>
          </message>
        """)

suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamTester)
