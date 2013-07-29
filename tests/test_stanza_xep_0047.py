import unittest
from sleekxmpp.exceptions import XMPPError
from sleekxmpp import Iq
from sleekxmpp.test import SleekTest
from sleekxmpp.plugins.xep_0047 import Data
from sleekxmpp.xmlstream import register_stanza_plugin, ET


class TestIBB(SleekTest):

    def setUp(self):
        register_stanza_plugin(Iq, Data)

    def testInvalidBase64MidEqual(self):
        """
        Test detecting invalid base64 data with = inside the
        character data instead of at the end.
        """
        iq = Iq(xml=ET.fromstring("""
          <iq type="set" id="0" to="tester@localhost">
            <data xmlns="http://jabber.org/protocol/ibb" seq="0">
              ABC=DEFGH
            </data>
          </iq>
        """))

        errored = False

        try:
            data = iq['ibb_data']['data']
        except XMPPError:
            errored = True

        self.assertTrue(errored, "ABC=DEFGH did not raise base64 error")

    def testInvalidBase64PrefixEqual(self):
        """
        Test detecting invalid base64 data with = as a prefix
        to the character data.
        """
        iq = Iq(xml=ET.fromstring("""
          <iq type="set" id="0" to="tester@localhost">
            <data xmlns="http://jabber.org/protocol/ibb" seq="0">
              =ABCDEFGH
            </data>
          </iq>
        """))

        errored = False

        try:
            data = iq['ibb_data']['data']
        except XMPPError:
            errored = True

        self.assertTrue(errored, "=ABCDEFGH did not raise base64 error")

    def testInvalidBase64Alphabet(self):
        """
        Test detecting invalid base64 data with characters
        outside of the base64 alphabet.
        """
        iq = Iq(xml=ET.fromstring("""
          <iq type="set" id="0" to="tester@localhost">
            <data xmlns="http://jabber.org/protocol/ibb" seq="0">
              ABCD?EFGH
            </data>
          </iq>
        """))

        errored = False

        try:
            data = iq['ibb_data']['data']
        except XMPPError:
            errored = True

        self.assertTrue(errored, "ABCD?EFGH did not raise base64 error")

    def testConvertData(self):
        """Test that data is converted to base64"""
        iq = Iq()
        iq['type'] = 'set'
        iq['ibb_data']['seq'] = 0
        iq['ibb_data']['data'] = 'sleekxmpp'

        self.check(iq, """
          <iq type="set">
            <data xmlns="http://jabber.org/protocol/ibb" seq="0">c2xlZWt4bXBw</data>
          </iq>
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestIBB)
