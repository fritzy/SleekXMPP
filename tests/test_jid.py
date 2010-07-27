from sleektest import *
from sleekxmpp.xmlstream.jid import JID

class TestJIDClass(SleekTest):
    def testJIDfromfull(self):
        j = JID('user@someserver/some/resource')
        self.assertEqual(j.user, 'user', "User does not match")
        self.assertEqual(j.domain, 'someserver', "Domain does not match")
        self.assertEqual(j.resource, 'some/resource', "Resource does not match")
        self.assertEqual(j.bare, 'user@someserver', "Bare does not match")
        self.assertEqual(j.full, 'user@someserver/some/resource', "Full does not match")
        self.assertEqual(str(j), 'user@someserver/some/resource', "String does not match")

    def testJIDchange(self):
        j = JID('user1@someserver1/some1/resource1')
        j.user = 'user'
        j.domain = 'someserver'
        j.resource = 'some/resource'
        self.assertEqual(j.user, 'user', "User does not match")
        self.assertEqual(j.domain, 'someserver', "Domain does not match")
        self.assertEqual(j.resource, 'some/resource', "Resource does not match")
        self.assertEqual(j.bare, 'user@someserver', "Bare does not match")
        self.assertEqual(j.full, 'user@someserver/some/resource', "Full does not match")
        self.assertEqual(str(j), 'user@someserver/some/resource', "String does not match")

suite = unittest.TestLoader().loadTestsFromTestCase(TestJIDClass)
