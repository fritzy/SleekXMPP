import logging

from sleekxmpp.test import *


class TestLiveStream(SleekTest):
    """
    Test that we can test a live stanza stream.
    """

    def tearDown(self):
        self.stream_close()

    def testClientConnection(self):
        """Test that we can interact with a live ClientXMPP instance."""
        self.stream_start(mode='client',
                          socket='live',
                          skip=False,
                          jid='user@localhost/test',
                          password='user')

        # Use sid=None to ignore any id sent by the server since
        # we can't know it in advance.
        self.recv_header(sfrom='localhost', sid=None)
        self.send_header(sto='localhost')
        self.recv_feature("""
          <stream:features>
            <starttls xmlns="urn:ietf:params:xml:ns:xmpp-tls" />
            <mechanisms xmlns="urn:ietf:params:xml:ns:xmpp-sasl">
              <mechanism>DIGEST-MD5</mechanism>
              <mechanism>PLAIN</mechanism>
            </mechanisms>
          </stream:features>
        """)
        self.send_feature("""
          <starttls xmlns="urn:ietf:params:xml:ns:xmpp-tls" />
        """)
        self.recv_feature("""
          <proceed xmlns="urn:ietf:params:xml:ns:xmpp-tls" />
        """)
        self.send_header(sto='localhost')
        self.recv_header(sfrom='localhost', sid=None)
        self.recv_feature("""
          <stream:features>
            <mechanisms xmlns="urn:ietf:params:xml:ns:xmpp-sasl">
              <mechanism>DIGEST-MD5</mechanism>
              <mechanism>PLAIN</mechanism>
            </mechanisms>
          </stream:features>
        """)
        self.send_feature("""
          <auth xmlns="urn:ietf:params:xml:ns:xmpp-sasl"
                mechanism="PLAIN">AHVzZXIAdXNlcg==</auth>
        """)
        self.recv_feature("""
          <success xmlns="urn:ietf:params:xml:ns:xmpp-sasl" />
        """)
        self.send_header(sto='localhost')
        self.recv_header(sfrom='localhost', sid=None)
        self.recv_feature("""
          <stream:features>
            <bind xmlns="urn:ietf:params:xml:ns:xmpp-bind" />
            <session xmlns="urn:ietf:params:xml:ns:xmpp-session" />
          </stream:features>
        """)

        # Should really use send, but our Iq stanza objects
        # can't handle bind element payloads yet.
        self.send_feature("""
          <iq type="set" id="1">
            <bind xmlns="urn:ietf:params:xml:ns:xmpp-bind">
              <resource>test</resource>
            </bind>
          </iq>
        """)
        self.recv_feature("""
          <iq type="result" id="1">
            <bind xmlns="urn:ietf:params:xml:ns:xmpp-bind">
              <jid>user@localhost/test</jid>
            </bind>
          </iq>
        """)
        self.stream_close()


suite = unittest.TestLoader().loadTestsFromTestCase(TestLiveStream)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    tests = unittest.TestSuite([suite])
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    test_ns = 'http://andyet.net/protocol/tests'
    print("<tests xmlns='%s' %s %s %s %s />" % (
        test_ns,
        'ran="%s"' % result.testsRun,
        'errors="%s"' % len(result.errors),
        'fails="%s"' % len(result.failures),
        'success="%s"' % result.wasSuccessful()))
