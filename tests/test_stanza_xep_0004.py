from sleekxmpp.test import *
import sleekxmpp.plugins.xep_0004 as xep_0004


class TestDataForms(SleekTest):

    def setUp(self):
        register_stanza_plugin(Message, xep_0004.Form)
        register_stanza_plugin(xep_0004.Form, xep_0004.FormField)
        register_stanza_plugin(xep_0004.FormField, xep_0004.FieldOption)

    def testMultipleInstructions(self):
        """Testing using multiple instructions elements in a data form."""
        msg = self.Message()
        msg['form']['instructions'] = "Instructions\nSecond batch"

        self.check(msg, """
          <message>
            <x xmlns="jabber:x:data" type="form">
              <instructions>Instructions</instructions>
              <instructions>Second batch</instructions>
            </x>
          </message>
        """)

    def testAddField(self):
        """Testing adding fields to a data form."""

        msg = self.Message()
        form = msg['form']
        form.addField(var='f1',
                      ftype='text-single',
                      label='Text',
                      desc='A text field',
                      required=True,
                      value='Some text!')

        self.check(msg, """
          <message>
            <x xmlns="jabber:x:data" type="form">
              <field var="f1" type="text-single" label="Text">
                <desc>A text field</desc>
                <required />
                <value>Some text!</value>
              </field>
            </x>
          </message>
        """)

        form['fields'] = [('f1', {'type': 'text-single',
                                  'label': 'Username',
                                  'required': True}),
                          ('f2', {'type': 'text-private',
                                  'label': 'Password',
                                  'required': True}),
                          ('f3', {'type': 'text-multi',
                                  'label': 'Message',
                                  'value': 'Enter message.\nA long one even.'}),
                          ('f4', {'type': 'list-single',
                                  'label': 'Message Type',
                                  'options': [{'label': 'Cool!',
                                               'value': 'cool'},
                                              {'label': 'Urgh!',
                                               'value': 'urgh'}]})]
        self.check(msg, """
          <message>
            <x xmlns="jabber:x:data" type="form">
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
        """)

    def testSetValues(self):
        """Testing setting form values"""

        msg = self.Message()
        form = msg['form']
        form.setFields([
                ('foo', {'type': 'text-single'}),
                ('bar', {'type': 'list-multi'})])

        form.setValues({'foo': 'Foo!',
                        'bar': ['a', 'b']})

        self.check(msg, """
          <message>
            <x xmlns="jabber:x:data" type="form">
              <field var="foo" type="text-single">
                <value>Foo!</value>
              </field>
              <field var="bar" type="list-multi">
                <value>a</value>
                <value>b</value>
              </field>
            </x>
          </message>""")

suite = unittest.TestLoader().loadTestsFromTestCase(TestDataForms)
