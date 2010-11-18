import logging

from sleekxmpp.test import *


class TestMultipleStreams(SleekTest):
    """
    Test that we can test a live stanza stream.
    """

    def setUp(self):
        self.client1 = SleekTest()
        self.client2 = SleekTest()

    def tearDown(self):
        self.client1.stream_close()
        self.client2.stream_close()

    def testMultipleStreams(self):
        """Test that we can interact with multiple live ClientXMPP instance."""

        client1 = self.client1
        client2 = self.client2

        client1.stream_start(mode='client',
                             socket='live',
                             skip=True,
                             jid='user@localhost/test1',
                             password='user')
        client2.stream_start(mode='client',
                             socket='live',
                             skip=True,
                             jid='user@localhost/test2',
                             password='user')

        client1.xmpp.send_message(mto='user@localhost/test2',
                                  mbody='test')

        client1.send('message@body=test', method='stanzapath')
        client2.recv('message@body=test', method='stanzapath')


suite = unittest.TestLoader().loadTestsFromTestCase(TestMultipleStreams)

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
