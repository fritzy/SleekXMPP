# -*- encoding:utf-8 -*-

from __future__ import unicode_literals

from sleekxmpp.test import *
import time
import threading


class TestStreamRoster(SleekTest):
    """
    Test handling roster updates.
    """

    def tearDown(self):
        self.stream_close()

    def testGetRoster(self):
        """Test handling roster requests."""
        self.stream_start(mode='client')
        self.failUnless(self.xmpp.roster == {}, "Initial roster not empty.")

        events = []

        def roster_received(iq):
            events.append('roster_received')

        self.xmpp.add_event_handler('roster_received', roster_received)

        # Since get_roster blocks, we need to run it in a thread.
        t = threading.Thread(name='get_roster', target=self.xmpp.get_roster)
        t.start()

        self.send("""
          <iq type="get" id="1">
            <query xmlns="jabber:iq:roster" />
          </iq>
        """)
        self.recv("""
          <iq type="result" id="1">
            <query xmlns="jabber:iq:roster">
              <item jid="user@localhost"
                    name="User"
                    subscription="both">
                <group>Friends</group>
                <group>Examples</group>
              </item>
            </query>
          </iq>
        """)

        # Wait for get_roster to return.
        t.join()

        # Give the event queue time to process.
        time.sleep(.1)

        roster = {'user@localhost': {'name': 'User',
                                     'subscription': 'both',
                                     'groups': ['Friends', 'Examples'],
                                     'presence': {},
                                     'in_roster': True}}
        self.failUnless(self.xmpp.roster == roster,
                "Unexpected roster values: %s" % self.xmpp.roster)
        self.failUnless('roster_received' in events,
                "Roster received event not triggered: %s" % events)

    def testRosterSet(self):
        """Test handling pushed roster updates."""
        self.stream_start(mode='client')
        self.failUnless(self.xmpp.roster == {}, "Initial roster not empty.")
        events = []

        def roster_update(e):
            events.append('roster_update')

        self.xmpp.add_event_handler('roster_update', roster_update)


        self.recv("""
          <iq type="set" id="1">
            <query xmlns="jabber:iq:roster">
              <item jid="user@localhost"
                    name="User"
                    subscription="both">
                <group>Friends</group>
                <group>Examples</group>
              </item>
            </query>
          </iq>
        """)
        self.send("""
          <iq type="result" id="1">
            <query xmlns="jabber:iq:roster" />
          </iq>
        """)

        # Give the event queue time to process.
        time.sleep(.1)

        roster = {'user@localhost': {'name': 'User',
                                     'subscription': 'both',
                                     'groups': ['Friends', 'Examples'],
                                     'presence': {},
                                     'in_roster': True}}
        self.failUnless(self.xmpp.roster == roster,
                "Unexpected roster values: %s" % self.xmpp.roster)
        self.failUnless('roster_update' in events,
                "Roster updated event not triggered: %s" % events)

    def testRosterTimeout(self):
        """Test handling a timed out roster request."""
        self.stream_start()
        events = []

        def roster_timeout(event):
            events.append('roster_timeout')

        self.xmpp.add_event_handler('roster_timeout', roster_timeout)
        self.xmpp.get_roster(timeout=0)

        # Give the event queue time to process.
        time.sleep(.1)

        self.failUnless(events == ['roster_timeout'],
                 "Roster timeout event not triggered: %s." % events)

    def testRosterCallback(self):
        """Test handling a roster request callback."""
        self.stream_start()
        events = []

        def roster_callback(iq):
            events.append('roster_callback')

        # Since get_roster blocks, we need to run it in a thread.
        t = threading.Thread(name='get_roster',
                             target=self.xmpp.get_roster,
                             kwargs={'callback': roster_callback})
        t.start()

        self.send("""
          <iq type="get" id="1">
            <query xmlns="jabber:iq:roster" />
          </iq>
        """)
        self.recv("""
          <iq type="result" id="1">
            <query xmlns="jabber:iq:roster">
              <item jid="user@localhost"
                    name="User"
                    subscription="both">
                <group>Friends</group>
                <group>Examples</group>
              </item>
            </query>
          </iq>
        """)

        # Wait for get_roster to return.
        t.join()

        # Give the event queue time to process.
        time.sleep(.1)

        self.failUnless(events == ['roster_callback'],
                 "Roster timeout event not triggered: %s." % events)

    def testRosterUnicode(self):
        """Test that JIDs with Unicode values are handled properly."""
        self.stream_start()
        self.recv("""
          <iq to="tester@localhost" type="set" id="1">
            <query xmlns="jabber:iq:roster">
              <item jid="andré@foo" subscription="both">
                <group>Unicode</group>
              </item>
            </query>
          </iq>
        """)

        # Give the event queue time to process.
        time.sleep(.1)

        roster = {'andré@foo': {
                    'name': '',
                    'subscription': 'both',
                    'groups': ['Unicode'],
                    'presence': {},
                    'in_roster': True}}
        self.failUnless(self.xmpp.roster == roster,
                "Unexpected roster values: %s" % self.xmpp.roster)

        self.recv("""
          <presence from="andré@foo/bar" />
        """)

        # Give the event queue time to process.
        time.sleep(.1)

        roster = {'andré@foo': {
                    'name': '',
                    'subscription': 'both',
                    'groups': ['Unicode'],
                    'presence': {
                        'bar':{'priority':0,
                               'status':'',
                               'show':'available'}},
                    'in_roster': True}}
        self.failUnless(self.xmpp.roster == roster,
                "Unexpected roster values: %s" % self.xmpp.roster)



suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamRoster)
