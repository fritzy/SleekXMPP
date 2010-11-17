from sleekxmpp.test import *
import sleekxmpp.plugins.gmail_notify as gmail


class TestGmail(SleekTest):

    def setUp(self):
        register_stanza_plugin(Iq, gmail.GmailQuery)
        register_stanza_plugin(Iq, gmail.MailBox)
        register_stanza_plugin(Iq, gmail.NewMail)

    def testCreateQuery(self):
        """Testing querying Gmail for emails."""

        iq = self.Iq()
        iq['type'] = 'get'
        iq['gmail']['search'] = 'is:starred'
        iq['gmail']['newer-than-time'] = '1140638252542'
        iq['gmail']['newer-than-tid'] = '11134623426430234'

        self.check(iq, """
          <iq type="get">
            <query xmlns="google:mail:notify"
                   newer-than-time="1140638252542"
                   newer-than-tid="11134623426430234"
                   q="is:starred" />
          </iq>
        """, use_values=False)

    def testMailBox(self):
        """Testing reading from Gmail mailbox result"""

        # Use the example from Google's documentation at
        # http://code.google.com/apis/talk/jep_extensions/gmail.html#notifications
        xml = ET.fromstring("""
          <iq type="result">
            <mailbox xmlns="google:mail:notify"
                     result-time='1118012394209'
                     url='http://mail.google.com/mail'
                     total-matched='95'
                     total-estimate='0'>
              <mail-thread-info tid='1172320964060972012'
                                participation='1'
                                messages='28'
                                date='1118012394209'
                                url='http://mail.google.com/mail?view=cv'>
                <senders>
                  <sender name='Me' address='romeo@gmail.com' originator='1' />
                  <sender name='Benvolio' address='benvolio@gmail.com' />
                  <sender name='Mercutio' address='mercutio@gmail.com' unread='1'/>
                </senders>
                <labels>act1scene3</labels>
                <subject>Put thy rapier up.</subject>
                <snippet>Ay, ay, a scratch, a scratch; marry, 'tis enough.</snippet>
              </mail-thread-info>
            </mailbox>
          </iq>
        """)

        iq = self.Iq(xml=xml)
        mailbox = iq['mailbox']
        self.failUnless(mailbox['result-time'] == '1118012394209', "result-time doesn't match")
        self.failUnless(mailbox['url'] == 'http://mail.google.com/mail', "url doesn't match")
        self.failUnless(mailbox['matched'] == '95', "total-matched incorrect")
        self.failUnless(mailbox['estimate'] == False, "total-estimate incorrect")
        self.failUnless(len(mailbox['threads']) == 1, "could not extract message threads")

        thread = mailbox['threads'][0]
        self.failUnless(thread['tid'] == '1172320964060972012', "thread tid doesn't match")
        self.failUnless(thread['participation'] == '1', "thread participation incorrect")
        self.failUnless(thread['messages'] == '28', "thread message count incorrect")
        self.failUnless(thread['date'] == '1118012394209', "thread date doesn't match")
        self.failUnless(thread['url'] == 'http://mail.google.com/mail?view=cv', "thread url doesn't match")
        self.failUnless(thread['labels'] == 'act1scene3', "thread labels incorrect")
        self.failUnless(thread['subject'] == 'Put thy rapier up.', "thread subject doesn't match")
        self.failUnless(thread['snippet'] == "Ay, ay, a scratch, a scratch; marry, 'tis enough.", "snippet doesn't match")
        self.failUnless(len(thread['senders']) == 3, "could not extract senders")

        sender1 = thread['senders'][0]
        self.failUnless(sender1['name'] == 'Me', "sender name doesn't match")
        self.failUnless(sender1['address'] == 'romeo@gmail.com', "sender address doesn't match")
        self.failUnless(sender1['originator'] == True, "sender originator incorrect")
        self.failUnless(sender1['unread'] == False, "sender unread incorrectly True")

        sender2 = thread['senders'][2]
        self.failUnless(sender2['unread'] == True, "sender unread incorrectly False")

suite = unittest.TestLoader().loadTestsFromTestCase(TestGmail)
