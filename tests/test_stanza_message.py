from sleekxmpp.test import *
from sleekxmpp.stanza.message import Message
from sleekxmpp.stanza.htmlim import HTMLIM


class TestMessageStanzas(SleekTest):

    def setUp(self):
        register_stanza_plugin(Message, HTMLIM)

    def testGroupchatReplyRegression(self):
        "Regression groupchat reply should be to barejid"
        msg = self.Message()
        msg['to'] = 'me@myserver.tld'
        msg['from'] = 'room@someservice.someserver.tld/somenick'
        msg['type'] = 'groupchat'
        msg['body'] = "this is a message"
        msg.reply()
        self.failUnless(str(msg['to']) == 'room@someservice.someserver.tld')

    def testAttribProperty(self):
        "Test attrib property returning self"
        msg = self.Message()
        msg.attrib.attrib.attrib['to'] = 'usr@server.tld'
        self.failUnless(str(msg['to']) == 'usr@server.tld')

    def testHTMLPlugin(self):
        "Test message/html/body stanza"
        msg = self.Message()
        msg['to'] = "fritzy@netflint.net/sleekxmpp"
        msg['body'] = "this is the plaintext message"
        msg['type'] = 'chat'
        p = ET.Element('{http://www.w3.org/1999/xhtml}p')
        p.text = "This is the htmlim message"
        msg['html']['body'] = p
        self.check(msg, """
          <message to="fritzy@netflint.net/sleekxmpp" type="chat">
            <body>this is the plaintext message</body>
            <html xmlns="http://jabber.org/protocol/xhtml-im">
              <body xmlns="http://www.w3.org/1999/xhtml">
                <p>This is the htmlim message</p>
             </body>
            </html>
          </message>""")

    def testNickPlugin(self):
        "Test message/nick/nick stanza."
        msg = self.Message()
        msg['nick']['nick'] = 'A nickname!'
        self.check(msg, """
          <message>
            <nick xmlns="http://jabber.org/nick/nick">A nickname!</nick>
          </message>
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestMessageStanzas)
