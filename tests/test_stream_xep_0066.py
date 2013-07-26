import threading

import unittest
from sleekxmpp.test import SleekTest


class TestOOB(SleekTest):

    def tearDown(self):
        self.stream_close()

    def testSendOOB(self):
        """Test sending an OOB transfer request."""
        self.stream_start(plugins=['xep_0066', 'xep_0030'])

        url = 'http://github.com/fritzy/SleekXMPP/blob/master/README'

        t = threading.Thread(
                name='send_oob',
                target=self.xmpp['xep_0066'].send_oob,
                args=('user@example.com', url),
                kwargs={'desc': 'SleekXMPP README'})

        t.start()

        self.send("""
          <iq to="user@example.com" type="set" id="1">
            <query xmlns="jabber:iq:oob">
              <url>http://github.com/fritzy/SleekXMPP/blob/master/README</url>
              <desc>SleekXMPP README</desc>
            </query>
          </iq>
        """)

        self.recv("""
          <iq id="1" type="result"
              to="tester@localhost"
              from="user@example.com" />
        """)

        t.join()


suite = unittest.TestLoader().loadTestsFromTestCase(TestOOB)
