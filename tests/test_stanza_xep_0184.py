from sleekxmpp.test import *
import sleekxmpp.plugins.xep_0184 as xep_0184


class TestReciept(SleekTest):

    def setUp(self):
        register_stanza_plugin(Message, xep_0184.Request)
        register_stanza_plugin(Message, xep_0184.Received)

    def testCreateRequest(self):
        request = """<message><request xmlns="urn:xmpp:receipts" /></message>"""

        msg = self.Message()

        self.assertEqual(msg['request_reciept'], False)

        msg['request_reciept'] = True
        self.check(msg, request, use_values=False)

    def testCreateReceived(self):
        received = """<message><received xmlns="urn:xmpp:receipts" id="1"/></message>"""

        msg = self.Message()
        msg['reciept_received']['id'] = '1'

        self.check(msg, received)

suite = unittest.TestLoader().loadTestsFromTestCase(TestReciept)
