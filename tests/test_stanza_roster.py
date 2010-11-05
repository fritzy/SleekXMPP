from sleekxmpp.test import *
from sleekxmpp.stanza.roster import Roster


class TestRosterStanzas(SleekTest):

    def testAddItems(self):
        """Test adding items to a roster stanza."""
        iq = self.Iq()
        iq['roster'].setItems({
            'user@example.com': {
                'name': 'User',
                'subscription': 'both',
                'groups': ['Friends', 'Coworkers']},
            'otheruser@example.com': {
                'name': 'Other User',
                'subscription': 'both',
                'groups': []}})
        self.check(iq, """
          <iq>
            <query xmlns="jabber:iq:roster">
              <item jid="user@example.com" name="User" subscription="both">
                <group>Friends</group>
                <group>Coworkers</group>
              </item>
              <item jid="otheruser@example.com" name="Other User"
                    subscription="both" />
            </query>
          </iq>
        """)

    def testGetItems(self):
        """Test retrieving items from a roster stanza."""
        xml_string = """
          <iq>
            <query xmlns="jabber:iq:roster">
              <item jid="user@example.com" name="User" subscription="both">
                <group>Friends</group>
                <group>Coworkers</group>
              </item>
              <item jid="otheruser@example.com" name="Other User"
                    subscription="both" />
            </query>
          </iq>
        """
        iq = self.Iq(ET.fromstring(xml_string))
        expected = {
            'user@example.com': {
                'name': 'User',
                'subscription': 'both',
                'groups': ['Friends', 'Coworkers']},
            'otheruser@example.com': {
                'name': 'Other User',
                'subscription': 'both',
                'groups': []}}
        debug = "Roster items don't match after retrieval."
        debug += "\nReturned: %s" % str(iq['roster']['items'])
        debug += "\nExpected: %s" % str(expected)
        self.failUnless(iq['roster']['items'] == expected, debug)

    def testDelItems(self):
        """Test clearing items from a roster stanza."""
        xml_string = """
          <iq>
            <query xmlns="jabber:iq:roster">
              <item jid="user@example.com" name="User" subscription="both">
                <group>Friends</group>
                <group>Coworkers</group>
              </item>
              <item jid="otheruser@example.com" name="Other User"
                    subscription="both" />
            </query>
          </iq>
        """
        iq = self.Iq(ET.fromstring(xml_string))
        del iq['roster']['items']
        self.check(iq, """
          <iq>
            <query xmlns="jabber:iq:roster" />
          </iq>
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestRosterStanzas)
