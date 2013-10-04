from sleekxmpp import Iq
import unittest
from sleekxmpp.test import SleekTest
from sleekxmpp.plugins.xep_0050 import Command
from sleekxmpp.xmlstream import register_stanza_plugin


class TestAdHocCommandStanzas(SleekTest):

    def setUp(self):
        register_stanza_plugin(Iq, Command)

    def testAction(self):
        """Test using the action attribute."""
        iq = self.Iq()
        iq['type'] = 'set'
        iq['command']['node'] = 'foo'

        iq['command']['action'] = 'execute'
        self.failUnless(iq['command']['action'] == 'execute')

        iq['command']['action'] = 'complete'
        self.failUnless(iq['command']['action'] == 'complete')

        iq['command']['action'] = 'cancel'
        self.failUnless(iq['command']['action'] == 'cancel')

    def testSetActions(self):
        """Test setting next actions in a command stanza."""
        iq = self.Iq()
        iq['type'] = 'result'
        iq['command']['node'] = 'foo'
        iq['command']['actions'] = ['prev', 'next']

        self.check(iq, """
          <iq id="0" type="result">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo">
              <actions>
                <prev />
                <next />
              </actions>
            </command>
          </iq>
        """)

    def testGetActions(self):
        """Test retrieving next actions from a command stanza."""
        iq = self.Iq()
        iq['command']['node'] = 'foo'
        iq['command']['actions'] = ['prev', 'next']

        results = iq['command']['actions']
        expected = set(['prev', 'next'])
        self.assertEqual(results, expected,
                         "Incorrect next actions: %s" % results)

    def testDelActions(self):
        """Test removing next actions from a command stanza."""
        iq = self.Iq()
        iq['type'] = 'result'
        iq['command']['node'] = 'foo'
        iq['command']['actions'] = ['prev', 'next']

        del iq['command']['actions']

        self.check(iq, """
          <iq id="0" type="result">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo" />
          </iq>
        """)

    def testAddNote(self):
        """Test adding a command note."""
        iq = self.Iq()
        iq['type'] = 'result'
        iq['command']['node'] = 'foo'
        iq['command'].add_note('Danger!', ntype='warning')

        self.check(iq, """
          <iq id="0" type="result">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo">
              <note type="warning">Danger!</note>
            </command>
          </iq>
        """)

    def testNotes(self):
        """Test using command notes."""
        iq = self.Iq()
        iq['type'] = 'result'
        iq['command']['node'] = 'foo'

        notes = [('info', 'Interesting...'),
                 ('warning', 'Danger!'),
                 ('error', "I can't let you do that")]
        iq['command']['notes'] = notes

        self.failUnless(iq['command']['notes'] == notes,
                "Notes don't match: %s %s" % (notes, iq['command']['notes']))

        self.check(iq, """
          <iq id="0" type="result">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo">
              <note type="info">Interesting...</note>
              <note type="warning">Danger!</note>
              <note type="error">I can't let you do that</note>
            </command>
          </iq>
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestAdHocCommandStanzas)
