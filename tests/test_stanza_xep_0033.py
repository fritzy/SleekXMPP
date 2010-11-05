from sleekxmpp.test import *
import sleekxmpp.plugins.xep_0033 as xep_0033


class TestAddresses(SleekTest):

    def setUp(self):
        register_stanza_plugin(Message, xep_0033.Addresses)

    def testAddAddress(self):
        """Testing adding extended stanza address."""
        msg = self.Message()
        msg['addresses'].addAddress(atype='to', jid='to@header1.org')
        self.check(msg, """
        <message>
          <addresses xmlns="http://jabber.org/protocol/address">
            <address jid="to@header1.org" type="to" />
          </addresses>
        </message>
        """)

        msg = self.Message()
        msg['addresses'].addAddress(atype='replyto',
                                    jid='replyto@header1.org',
                                    desc='Reply address')
        self.check(msg, """
          <message>
            <addresses xmlns="http://jabber.org/protocol/address">
              <address jid="replyto@header1.org" type="replyto" desc="Reply address" />
            </addresses>
          </message>
        """)

    def testAddAddresses(self):
        """Testing adding multiple extended stanza addresses."""

        xmlstring = """
          <message>
            <addresses xmlns="http://jabber.org/protocol/address">
              <address jid="replyto@header1.org" type="replyto" desc="Reply address" />
              <address jid="cc@header2.org" type="cc" />
              <address jid="bcc@header2.org" type="bcc" />
            </addresses>
          </message>
        """

        msg = self.Message()
        msg['addresses'].setAddresses([
            {'type':'replyto',
             'jid':'replyto@header1.org',
             'desc':'Reply address'},
            {'type':'cc',
             'jid':'cc@header2.org'},
            {'type':'bcc',
             'jid':'bcc@header2.org'}])
        self.check(msg, xmlstring)

        msg = self.Message()
        msg['addresses']['replyto'] = [{'jid':'replyto@header1.org',
                                                'desc':'Reply address'}]
        msg['addresses']['cc'] = [{'jid':'cc@header2.org'}]
        msg['addresses']['bcc'] = [{'jid':'bcc@header2.org'}]
        self.check(msg, xmlstring)

    def testAddURI(self):
        """Testing adding URI attribute to extended stanza address."""

        msg = self.Message()
        addr = msg['addresses'].addAddress(atype='to',
                                           jid='to@header1.org',
                                           node='foo')
        self.check(msg, """
          <message>
            <addresses xmlns="http://jabber.org/protocol/address">
              <address node="foo" jid="to@header1.org" type="to" />
            </addresses>
          </message>
        """)

        addr['uri'] = 'mailto:to@header2.org'
        self.check(msg, """
          <message>
            <addresses xmlns="http://jabber.org/protocol/address">
              <address type="to" uri="mailto:to@header2.org" />
            </addresses>
          </message>
        """)

    def testDelivered(self):
        """Testing delivered attribute of extended stanza addresses."""

        xmlstring = """
          <message>
            <addresses xmlns="http://jabber.org/protocol/address">
              <address %s jid="to@header1.org" type="to" />
            </addresses>
          </message>
        """

        msg = self.Message()
        addr = msg['addresses'].addAddress(jid='to@header1.org', atype='to')
        self.check(msg, xmlstring % '')

        addr['delivered'] = True
        self.check(msg, xmlstring % 'delivered="true"')

        addr['delivered'] = False
        self.check(msg, xmlstring % '')


suite = unittest.TestLoader().loadTestsFromTestCase(TestAddresses)
