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

        self.recv("""
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
        self.recv("""
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
        self.recv("""
          <presence from="otheruser@localhost/foobar" />
        """)

        # Contact goes offline, should trigger got_offline.
        self.recv("""
          <presence from="otheruser@localhost/foobar"
                    type="unavailable" />
        """)

        # Give event queue time to process.
        time.sleep(0.1)

        self.assertEqual(events, ['got_offline'],
                "Got offline incorrectly triggered: %s" % events)

    def testGotOnline(self):
        """Test that got_online is triggered properly."""

        events = set()

        def presence_available(p):
            events.add('presence_available')

        def got_online(p):
            events.add('got_online')

        self.stream_start()
        self.xmpp.add_event_handler('presence_available', presence_available)
        self.xmpp.add_event_handler('got_online', got_online)

        self.recv("""
          <presence from="user@localhost" />
        """)

        # Give event queue time to process.
        time.sleep(0.1)

        expected = set(('presence_available', 'got_online'))
        self.assertEqual(events, expected,
                "Incorrect events triggered: %s" % events)

    def testAutoAuthorizeAndSubscribe(self):
        """
        Test auto authorizing and auto subscribing
        to subscription requests.
        """

        events = set()

        def presence_subscribe(p):
            events.add('presence_subscribe')

        def changed_subscription(p):
            events.add('changed_subscription')

        self.stream_start(jid='tester@localhost')

        self.xmpp.add_event_handler('changed_subscription',
                                    changed_subscription)
        self.xmpp.add_event_handler('presence_subscribe',
                                    presence_subscribe)

        # With these settings we should accept a subscription
        # and request a subscription in return.
        self.xmpp.auto_authorize = True
        self.xmpp.auto_subscribe = True

        self.recv("""
          <presence from="user@localhost" type="subscribe" />
        """)

        self.send("""
          <presence to="user@localhost" type="subscribed" />
        """)

        self.send("""
          <presence to="user@localhost" type="subscribe" />
        """)

        expected = set(('presence_subscribe', 'changed_subscription'))
        self.assertEqual(events, expected,
                "Incorrect events triggered: %s" % events)

    def testNoAutoAuthorize(self):
        """Test auto rejecting subscription requests."""

        events = set()

        def presence_subscribe(p):
            events.add('presence_subscribe')

        def changed_subscription(p):
            events.add('changed_subscription')

        self.stream_start(jid='tester@localhost')

        self.xmpp.add_event_handler('changed_subscription',
                                    changed_subscription)
        self.xmpp.add_event_handler('presence_subscribe',
                                    presence_subscribe)

        # With this setting we should reject all subscriptions.
        self.xmpp.auto_authorize = False

        self.recv("""
          <presence from="user@localhost" type="subscribe" />
        """)

        self.send("""
          <presence to="user@localhost" type="unsubscribed" />
        """)

        expected = set(('presence_subscribe', 'changed_subscription'))
        self.assertEqual(events, expected,
                "Incorrect events triggered: %s" % events)


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamPresence)
