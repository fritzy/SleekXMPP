from sleekxmpp.test import *
import sleekxmpp.plugins.xep_0085 as xep_0085

class TestChatStates(SleekTest):

    def setUp(self):
        register_stanza_plugin(Message, xep_0085.Active)
        register_stanza_plugin(Message, xep_0085.Composing)
        register_stanza_plugin(Message, xep_0085.Gone)
        register_stanza_plugin(Message, xep_0085.Inactive)
        register_stanza_plugin(Message, xep_0085.Paused)

    def testCreateChatState(self):
        """Testing creating chat states."""

        xmlstring = """
          <message>
            <%s xmlns="http://jabber.org/protocol/chatstates" />
          </message>
        """

        msg = self.Message()
        msg['chat_state'].active()
        self.check(msg, xmlstring % 'active',
                          use_values=False)

        msg['chat_state'].composing()
        self.check(msg, xmlstring % 'composing',
                          use_values=False)


        msg['chat_state'].gone()
        self.check(msg, xmlstring % 'gone',
                          use_values=False)

        msg['chat_state'].inactive()
        self.check(msg, xmlstring % 'inactive',
                          use_values=False)

        msg['chat_state'].paused()
        self.check(msg, xmlstring % 'paused',
                          use_values=False)

suite = unittest.TestLoader().loadTestsFromTestCase(TestChatStates)
