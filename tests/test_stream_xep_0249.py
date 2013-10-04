import time

import unittest
from sleekxmpp.test import SleekTest


class TestStreamDirectInvite(SleekTest):

    """
    Test using the XEP-0249 plugin.
    """

    def tearDown(self):
        self.stream_close()

    def testReceiveInvite(self):
        self.stream_start(mode='client',
                          plugins=['xep_0030',
                                   'xep_0249'])

        events = []

        def handle_invite(msg):
            events.append(True)

        self.xmpp.add_event_handler('groupchat_direct_invite',
                                    handle_invite)

        self.recv("""
          <message>
            <x xmlns="jabber:x:conference"
               jid="sleek@conference.jabber.org"
               password="foo"
               reason="For testing" />
          </message>
        """)

        time.sleep(.5)

        self.failUnless(events == [True],
                "Event not raised: %s" % events)

    def testSentDirectInvite(self):
        self.stream_start(mode='client',
                          plugins=['xep_0030',
                                   'xep_0249'])

        self.xmpp['xep_0249'].send_invitation('user@example.com',
                                              'sleek@conference.jabber.org',
                                              reason='Need to test Sleek')

        self.send("""
          <message to="user@example.com">
            <x xmlns="jabber:x:conference"
               jid="sleek@conference.jabber.org"
               reason="Need to test Sleek" />
          </message>
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamDirectInvite)
