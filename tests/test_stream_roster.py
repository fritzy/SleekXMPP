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

        roster = {'user@localhost': {'name': 'User',
                                     'subscription': 'both',
                                     'groups': ['Friends', 'Examples'],
                                     'presence': {},
                                     'in_roster': True}}
        self.failUnless(self.xmpp.roster == roster,
                "Unexpected roster values: %s" % self.xmpp.roster)

    def testRosterSet(self):
        """Test handling pushed roster updates."""
        self.stream_start(mode='client')
        self.failUnless(self.xmpp.roster == {}, "Initial roster not empty.")

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

        roster = {'user@localhost': {'name': 'User',
                                     'subscription': 'both',
                                     'groups': ['Friends', 'Examples'],
                                     'presence': {},
                                     'in_roster': True}}
        self.failUnless(self.xmpp.roster == roster,
                "Unexpected roster values: %s" % self.xmpp.roster)




suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamRoster)
