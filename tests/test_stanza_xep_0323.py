from sleekxmpp.test import *
import sleekxmpp.plugins.xep_0323 as xep_0323

namespace='sn'

class TestChatStates(SleekTest):
    

    def setUp(self):
        register_stanza_plugin(Message, xep_0323.stanza.Request)
        register_stanza_plugin(Message, xep_0323.stanza.Accepted)
        register_stanza_plugin(Message, xep_0323.stanza.Failure)
        # register_stanza_plugin(Message, xep_0323.stanza.Result)
        # register_stanza_plugin(Message, xep_0323.stanza.Gone)
        # register_stanza_plugin(Message, xep_0323.stanza.Inactive)
        # register_stanza_plugin(Message, xep_0323.stanza.Paused)

    def testRequest(self):
        """
        test of request stanza
        """
        iq = self.Iq()
        iq['type'] = 'get'
        iq['id'] = '1'
        iq['sensordata']['req']['seqnr'] = '1'
        iq['sensordata']['req']['momentary'] = 'true'

        self.check(iq,"""
        """
            )

    def testAccepted(self):
        """
        test of request stanza
        """
        iq = self.Iq()
        iq['type'] = 'result'
        iq['id'] = '2'
        iq['sensordata']['accepted']['seqnr'] = '2'

        print(str(iq))
        self.check(iq,"""
        """
            )
        
    def testReadOutMomentary_multiple(self):
        """
        test of reading momentary value from a nde with multiple responses
        """
        iq = self.Iq()        
        print(str(iq))

        self.check(iq,"""
        """
            )
    
suite = unittest.TestLoader().loadTestsFromTestCase(TestChatStates)
