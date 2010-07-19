from sleektest import *
import sleekxmpp.plugins.xep_0085 as xep_0085

class TestChatStates(SleekTest):

	def setUp(self):
		registerStanzaPlugin(Message, xep_0085.Active)
		registerStanzaPlugin(Message, xep_0085.Composing)
		registerStanzaPlugin(Message, xep_0085.Gone)
		registerStanzaPlugin(Message, xep_0085.Inactive)
		registerStanzaPlugin(Message, xep_0085.Paused)
        
	def testCreateChatState(self):
		"""Testing creating chat states."""
		
                xmlstring = """
                  <message>
                    <%s xmlns="http://jabber.org/protocol/chatstates" />
                  </message>
                """

		msg = self.Message()
		msg['chat_state'].active()
		self.checkMessage(msg, xmlstring % 'active', 
                                  use_values=False)

		msg['chat_state'].composing()
		self.checkMessage(msg, xmlstring % 'composing',
                                  use_values=False)


		msg['chat_state'].gone()
		self.checkMessage(msg, xmlstring % 'gone', 
                                  use_values=False)

		msg['chat_state'].inactive()
		self.checkMessage(msg, xmlstring % 'inactive', 
                                  use_values=False)

		msg['chat_state'].paused()
		self.checkMessage(msg, xmlstring % 'paused', 
                                  use_values=False)

suite = unittest.TestLoader().loadTestsFromTestCase(TestChatStates)
