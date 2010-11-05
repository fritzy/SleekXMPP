from sleekxmpp.test import *
from sleekxmpp.stanza.presence import Presence


class TestPresenceStanzas(SleekTest):

    def testPresenceShowRegression(self):
        """Regression check presence['type'] = 'dnd' show value working"""
        p = self.Presence()
        p['type'] = 'dnd'
        self.check(p, "<presence><show>dnd</show></presence>")

    def testPresenceType(self):
        """Test manipulating presence['type']"""
        p = self.Presence()
        p['type'] = 'available'
        self.check(p, "<presence />")
        self.failUnless(p['type'] == 'available',
            "Incorrect presence['type'] for type 'available': %s" % p['type'])

        for showtype in ['away', 'chat', 'dnd', 'xa']:
            p['type'] = showtype
            self.check(p, """
              <presence><show>%s</show></presence>
            """ % showtype)
            self.failUnless(p['type'] == showtype,
                "Incorrect presence['type'] for type '%s'" % showtype)

        p['type'] = None
        self.check(p, "<presence />")

    def testPresenceUnsolicitedOffline(self):
        """
        Unsolicted offline presence does not spawn changed_status
        or update the roster.
        """
        p = self.Presence()
        p['type'] = 'unavailable'
        p['from'] = 'bill@chadmore.com/gmail15af'

        c = sleekxmpp.ClientXMPP('crap@wherever', 'password')
        happened = []

        def handlechangedpresence(event):
            happened.append(True)

        c.add_event_handler("changed_status", handlechangedpresence)
        c._handle_presence(p)

        self.failUnless(happened == [],
            "changed_status event triggered for extra unavailable presence")
        self.failUnless(c.roster == {},
            "Roster updated for superfulous unavailable presence")

    def testNickPlugin(self):
        """Test presence/nick/nick stanza."""
        p = self.Presence()
        p['nick']['nick'] = 'A nickname!'
        self.check(p, """
          <presence>
            <nick xmlns="http://jabber.org/nick/nick">A nickname!</nick>
          </presence>
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestPresenceStanzas)
