import time

from sleekxmpp import Message
import unittest
from sleekxmpp.test import SleekTest


class TestFilters(SleekTest):

    """
    Test using incoming and outgoing filters.
    """

    def setUp(self):
        self.stream_start()

    def tearDown(self):
        self.stream_close()

    def testIncoming(self):

        data = []

        def in_filter(stanza):
            if isinstance(stanza, Message):
                if stanza['body'] == 'testing':
                    stanza['subject'] = stanza['body'] + ' filter'
                    print('>>> %s' % stanza['subject'])
            return stanza

        def on_message(msg):
            print('<<< %s' % msg['subject'])
            data.append(msg['subject'])

        self.xmpp.add_filter('in', in_filter)
        self.xmpp.add_event_handler('message', on_message)

        self.recv("""
          <message>
            <body>no filter</body>
          </message>
        """)

        self.recv("""
          <message>
            <body>testing</body>
          </message>
        """)

        time.sleep(0.5)

        self.assertEqual(data, ['', 'testing filter'],
                'Incoming filter did not apply %s' % data)

    def testOutgoing(self):

        def out_filter(stanza):
            if isinstance(stanza, Message):
                if stanza['body'] == 'testing':
                    stanza['body'] = 'changed!'
            return stanza

        self.xmpp.add_filter('out', out_filter)

        m1 = self.Message()
        m1['body'] = 'testing'
        m1.send()

        m2 = self.Message()
        m2['body'] = 'blah'
        m2.send()

        self.send("""
          <message>
            <body>changed!</body>
          </message>
        """)

        self.send("""
          <message>
            <body>blah</body>
          </message>
        """)



suite = unittest.TestLoader().loadTestsFromTestCase(TestFilters)
