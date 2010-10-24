import time
from sleekxmpp.test import *


class TestStreamPresence(SleekTest):
    """
    Test handling roster updates.
    """

    def tearDown(self):
        self.stream_close()

    def testInitialUnavailablePresences(self):
        """
        Test receiving unavailable presences from JIDs that
        are not online.
        """
        events = set()

        def got_offline(presence):
            # The got_offline event should not be triggered.
            events.add('got_offline')

        def unavailable(presence):
            # The presence_unavailable event should be triggered.
            events.add('unavailable')

        self.stream_start()
        self.xmpp.add_event_handler('got_offline', got_offline)
        self.xmpp.add_event_handler('presence_unavailable', unavailable)

        self.stream_recv("""
          <presence type="unavailable" from="otheruser@localhost" />
        """)

        # Give event queue time to process.
        time.sleep(0.1)

        self.assertEqual(events, set(('unavailable',)),
                "Got offline incorrectly triggered: %s." % events)

    def testGotOffline(self):
        """Test that got_offline is triggered properly."""
        events = []
        def got_offline(presence):
            events.append('got_offline')

        self.stream_start()
        self.xmpp.add_event_handler('got_offline', got_offline)

        # Setup roster. Use a 'set' instead of 'result' so we
        # don't have to handle get_roster() blocking.
        #
        # We use the stream to initialize the roster to make
        # the test independent of the roster implementation.
        self.stream_recv("""
          <iq type="set">
            <query xmlns="jabber:iq:roster">
              <item jid="otheruser@localhost"
                    name="Other User"
                    subscription="both">
                <group>Testers</group>
              </item>
            </query>
          </iq>
        """)

        # Contact comes online.
        self.stream_recv("""
          <presence from="otheruser@localhost/foobar" />
        """)

        # Contact goes offline, should trigger got_offline.
        self.stream_recv("""
          <presence from="otheruser@localhost/foobar"
                    type="unavailable" />
        """)

        # Give event queue time to process.
        time.sleep(0.1)

        self.assertEqual(events, ['got_offline'],
                "Got offline incorrectly triggered: %s" % events)


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamPresence)
