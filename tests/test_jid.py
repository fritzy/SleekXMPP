from sleekxmpp.test import *
from sleekxmpp.xmlstream.jid import JID


class TestJIDClass(SleekTest):

    """Verify that the JID class can parse and manipulate JIDs."""

    def testJIDFromFull(self):
        """Test using JID of the form 'user@server/resource/with/slashes'."""
        self.check_jid(JID('user@someserver/some/resource'),
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
        self.check_jid(j,
                       'user',
                       'someserver',
                       'some/resource',
                       'user@someserver',
                       'user@someserver/some/resource',
                       'user@someserver/some/resource')

    def testJIDaliases(self):
        """Test changing JID using aliases for domain."""
        j = JID('user@someserver/resource')
        j.server = 'anotherserver'
        self.check_jid(j, domain='anotherserver')
        j.host = 'yetanother'
        self.check_jid(j, domain='yetanother')

    def testJIDSetFullWithUser(self):
        """Test setting the full JID with a user portion."""
        j = JID('user@domain/resource')
        j.full = 'otheruser@otherdomain/otherresource'
        self.check_jid(j,
                       'otheruser',
                       'otherdomain',
                       'otherresource',
                       'otheruser@otherdomain',
                       'otheruser@otherdomain/otherresource',
                       'otheruser@otherdomain/otherresource')

    def testJIDFullNoUserWithResource(self):
        """
        Test setting the full JID without a user
        portion and with a resource.
        """
        j = JID('user@domain/resource')
        j.full = 'otherdomain/otherresource'
        self.check_jid(j,
                       '',
                       'otherdomain',
                       'otherresource',
                       'otherdomain',
                       'otherdomain/otherresource',
                       'otherdomain/otherresource')

    def testJIDFullNoUserNoResource(self):
        """
        Test setting the full JID without a user
        portion and without a resource.
        """
        j = JID('user@domain/resource')
        j.full = 'otherdomain'
        self.check_jid(j,
                       '',
                       'otherdomain',
                       '',
                       'otherdomain',
                       'otherdomain',
                       'otherdomain')

    def testJIDBareUser(self):
        """Test setting the bare JID with a user."""
        j = JID('user@domain/resource')
        j.bare = 'otheruser@otherdomain'
        self.check_jid(j,
                       'otheruser',
                       'otherdomain',
                       'resource',
                       'otheruser@otherdomain',
                       'otheruser@otherdomain/resource',
                       'otheruser@otherdomain/resource')

    def testJIDBareNoUser(self):
        """Test setting the bare JID without a user."""
        j = JID('user@domain/resource')
        j.bare = 'otherdomain'
        self.check_jid(j,
                       '',
                       'otherdomain',
                       'resource',
                       'otherdomain',
                       'otherdomain/resource',
                       'otherdomain/resource')

    def testJIDNoResource(self):
        """Test using JID of the form 'user@domain'."""
        self.check_jid(JID('user@someserver'),
                       'user',
                       'someserver',
                       '',
                       'user@someserver',
                       'user@someserver',
                       'user@someserver')

    def testJIDNoUser(self):
        """Test JID of the form 'component.domain.tld'."""
        self.check_jid(JID('component.someserver'),
                       '',
                       'component.someserver',
                       '',
                       'component.someserver',
                       'component.someserver',
                       'component.someserver')


suite = unittest.TestLoader().loadTestsFromTestCase(TestJIDClass)
