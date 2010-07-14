from sleektest import *
import sleekxmpp.plugins.alt_0004 as xep_0004


class TestDataForms(SleekTest):

    def setUp(self):
        self.stanzaPlugin(Message, xep_0004.Form)
        self.stanzaPlugin(xep_0004.Form, xep_0004.FormField)
        self.stanzaPlugin(xep_0004.FormField, xep_0004.FieldOption)

    def testMultipleInstructions(self):
        """Testing using multiple instructions elements in a data form."""
        msg = self.Message()
        msg['form']['instructions'] = "Instructions\nSecond batch"

        self.checkMessage(msg, """
          <message>
            <x xmlns="jabber:x:data">
              <instructions>Instructions</instructions>
              <instructions>Second batch</instructions>
            </x>
          </message>
        """, use_values=False)

    def testAddField(self):
        """Testing adding fields to a data form."""

        msg = self.Message()
        form = msg['form']
        form.addField('f1', 
                      ftype='text-single', 
                      label='Text',
                      desc='A text field', 
                      required=True, 
                      value='Some text!')

        self.checkMessage(msg, """
          <message>
            <x xmlns="jabber:x:data">
              <field var="f1" type="text-single" label="Text">
                <desc>A text field</desc>
                <required />
                <value>Some text!</value>
              </field>
            </x>
          </message>
        """, use_values=False)

        form['fields'] = {'f1': {'type': 'text-single', 
                                 'label': 'Username', 
                                 'required': True},
                          'f2': {'type': 'text-private',
                                 'label': 'Password',
                                 'required': True},
                          'f3': {'type': 'text-multi',
                                 'label': 'Message',
                                 'value': 'Enter message.\nA long one even.'},
                          'f4': {'type': 'list-single',
                                 'label': 'Message Type',
                                 'options': [{'label': 'Cool!', 
                                              'value': 'cool'},
                                             {'label': 'Urgh!',
                                              'value': 'urgh'}]}}
        self.checkMessage(msg, """
          <message>
            <x xmlns="jabber:x:data">
              <field var="f1" type="text-single" label="Username">
                <required />
              </field>
              <field var="f2" type="text-private" label="Password">
                <required />
              </field>
              <field var="f3" type="text-multi" label="Message">
                <value>Enter message.</value>
                <value>A long one even.</value>
              </field>
              <field var="f4" type="list-single" label="Message Type">
                <option label="Cool!">
                  <value>cool</value>
                </option>
                <option label="Urgh!">
                  <value>urgh</value>
                </option>
              </field>
            </x>
          </message>
        """, use_values=False)

suite = unittest.TestLoader().loadTestsFromTestCase(TestDataForms)
