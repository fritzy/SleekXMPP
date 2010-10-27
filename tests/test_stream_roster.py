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
        self.stream_start(mode='client', jid='tester@localhost')

        # Since get_roster blocks, we need to run it in a thread.
        t = threading.Thread(name='get_roster', target=self.xmpp.get_roster)
        t.start()

        self.send("""
          <iq type="get" id="1">
            <query xmlns="jabber:iq:roster" />
          </iq>
        """)
        self.recv("""
          <iq to='tester@localhost' type="result" id="1">
            <query xmlns="jabber:iq:roster">
              <item jid="user@localhost"
                    name="User"
                    subscription="from"
                    ask="subscribe">
                <group>Friends</group>
                <group>Examples</group>
              </item>
            </query>
          </iq>
        """)

        # Wait for get_roster to return.
        t.join()

        self.check_roster('tester@localhost', 'user@localhost',
                          name='User',
                          subscription='from',
                          afrom=True,
                          pending_out=True,
                          groups=['Friends', 'Examples'])

    def testRosterSet(self):
        """Test handling pushed roster updates."""
        self.stream_start(mode='client', jid='tester@localhost')

        self.recv("""
          <iq to='tester@localhost' type="set" id="1">
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

        self.check_roster('tester@localhost', 'user@localhost',
                          name='User',
                          subscription='both',
                          groups=['Friends', 'Examples'])


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamRoster)
