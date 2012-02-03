import threading
import time

from sleekxmpp.test import *


class TestInBandByteStreams(SleekTest):
    
    def setUp(self):
        self.stream_start(plugins=['xep_0047', 'xep_0030'])

    def tearDown(self):
        self.stream_close()

    def testOpenStream(self):
        """Test requesting a stream, successfully""" 

        events = []

        def on_stream_start(stream):
            events.append('ibb_stream_start')


        self.xmpp.add_event_handler('ibb_stream_start', on_stream_start)
    
        t = threading.Thread(name='open_stream',
                             target=self.xmpp['xep_0047'].open_stream,
                             args=('tester@localhost/receiver',),
                             kwargs={'sid': 'testing'})
        t.start()

        self.send("""
          <iq type="set" to="tester@localhost/receiver" id="1">
            <open xmlns="http://jabber.org/protocol/ibb" 
                  sid="testing"
                  block-size="4096"
                  stanza="iq" />
          </iq>
        """)

        self.recv("""
          <iq type="result" id="1"
              to="tester@localhost"
              from="tester@localhost/receiver" />
        """)

        t.join()

        time.sleep(0.2)

        self.assertEqual(events, ['ibb_stream_start'])

    def testAysncOpenStream(self):
        """Test requesting a stream, aysnc"""

        events = set()

        def on_stream_start(stream):
            events.add('ibb_stream_start')

        def stream_callback(iq):
            events.add('callback')

        self.xmpp.add_event_handler('ibb_stream_start', on_stream_start)
    
        t = threading.Thread(name='open_stream',
                             target=self.xmpp['xep_0047'].open_stream,
                             args=('tester@localhost/receiver',),
                             kwargs={'sid': 'testing', 
                                     'block': False,
                                     'callback': stream_callback})
        t.start()

        self.send("""
          <iq type="set" to="tester@localhost/receiver" id="1">
            <open xmlns="http://jabber.org/protocol/ibb" 
                  sid="testing"
                  block-size="4096"
                  stanza="iq" />
          </iq>
        """)

        self.recv("""
          <iq type="result" id="1"
              to="tester@localhost"
              from="tester@localhost/receiver" />
        """)

        t.join()

        time.sleep(0.2)

        self.assertEqual(events, set(['ibb_stream_start', 'callback']))




suite = unittest.TestLoader().loadTestsFromTestCase(TestInBandByteStreams)
