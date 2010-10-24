from sleekxmpp.test import *
from sleekxmpp.xmlstream.jid import JID


class TestJIDClass(SleekTest):

    """Verify that the JID class can parse and manipulate JIDs."""

    def testJIDfromfull(self):
        """Test using JID of the form 'user@server/resource/with/slashes'."""
        self.check_JID(JID('user@someserver/some/resource'),
                       'user',
                       'someserver',
                       'some/resource',
                       'user@someserver',
                       'user@someserver/some/resource',
                       'user@someserver/some/resource')

    def testJIDchange(self):
        """Test changing JID of the form 'user@server/resource/with/slashes'"""
        j = JID('user1@someserver1/some1/resource1')
        j.user = 'user'
        j.domain = 'someserver'
        j.resource = 'some/resource'
        self.check_JID(j,
                       'user',
                       'someserver',
                       'some/resource',
                       'user@someserver',
                       'user@someserver/some/resource',
                       'user@someserver/some/resource')

    def testJIDnoresource(self):
        """Test using JID of the form 'user@domain'."""
        self.check_JID(JID('user@someserver'),
                       'user',
                       'someserver',
                       '',
                       'user@someserver',
                       'user@someserver',
                       'user@someserver')

    def testJIDnouser(self):
        """Test JID of the form 'component.domain.tld'."""
        self.check_JID(JID('component.someserver'),
                       '',
                       'component.someserver',
                       '',
                       'component.someserver',
                       'component.someserver',
                       'component.someserver')


suite = unittest.TestLoader().loadTestsFromTestCase(TestJIDClass)
