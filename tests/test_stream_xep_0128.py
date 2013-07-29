import unittest
from sleekxmpp.test import SleekTest


class TestStreamExtendedDisco(SleekTest):

    """
    Test using the XEP-0128 plugin.
    """

    def tearDown(self):
        self.stream_close()

    def testUsingExtendedInfo(self):
        self.stream_start(mode='client',
                          jid='tester@localhost',
                          plugins=['xep_0030',
                                   'xep_0004',
                                   'xep_0128'])

        form = self.xmpp['xep_0004'].makeForm(ftype='result')
        form.addField(var='FORM_TYPE', ftype='hidden', value='testing')

        info_ns = 'http://jabber.org/protocol/disco#info'
        self.xmpp['xep_0030'].add_identity(node='test',
                                           category='client',
                                           itype='bot')
        self.xmpp['xep_0030'].add_feature(node='test', feature=info_ns)
        self.xmpp['xep_0128'].set_extended_info(node='test', data=form)

        self.recv("""
          <iq type="get" id="test" to="tester@localhost">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="test" />
          </iq>
        """)

        self.send("""
          <iq type="result" id="test">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="test">
              <identity category="client" type="bot" />
              <feature var="http://jabber.org/protocol/disco#info" />
              <x xmlns="jabber:x:data" type="result">
                <field var="FORM_TYPE" type="hidden">
                  <value>testing</value>
                </field>
              </x>
            </query>
          </iq>
        """)

    def testUsingMultipleExtendedInfo(self):
        self.stream_start(mode='client',
                          jid='tester@localhost',
                          plugins=['xep_0030',
                                   'xep_0004',
                                   'xep_0128'])

        form1 = self.xmpp['xep_0004'].makeForm(ftype='result')
        form1.addField(var='FORM_TYPE', ftype='hidden', value='testing')

        form2 = self.xmpp['xep_0004'].makeForm(ftype='result')
        form2.addField(var='FORM_TYPE', ftype='hidden', value='testing_2')

        info_ns = 'http://jabber.org/protocol/disco#info'
        self.xmpp['xep_0030'].add_identity(node='test',
                                           category='client',
                                           itype='bot')
        self.xmpp['xep_0030'].add_feature(node='test', feature=info_ns)
        self.xmpp['xep_0128'].set_extended_info(node='test', data=[form1, form2])

        self.recv("""
          <iq type="get" id="test" to="tester@localhost">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="test" />
          </iq>
        """)

        self.send("""
          <iq type="result" id="test">
            <query xmlns="http://jabber.org/protocol/disco#info"
                   node="test">
              <identity category="client" type="bot" />
              <feature var="http://jabber.org/protocol/disco#info" />
              <x xmlns="jabber:x:data" type="result">
                <field var="FORM_TYPE" type="hidden">
                  <value>testing</value>
                </field>
              </x>
              <x xmlns="jabber:x:data" type="result">
                <field var="FORM_TYPE" type="hidden">
                  <value>testing_2</value>
                </field>
              </x>
            </query>
          </iq>
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamExtendedDisco)
