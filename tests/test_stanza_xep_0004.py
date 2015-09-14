import unittest
from sleekxmpp import Message
from sleekxmpp.test import SleekTest
from sleekxmpp.thirdparty import OrderedDict

import sleekxmpp.plugins.xep_0004 as xep_0004
from sleekxmpp.xmlstream import register_stanza_plugin


class TestDataForms(SleekTest):

    def setUp(self):
        register_stanza_plugin(Message, xep_0004.Form)
        register_stanza_plugin(xep_0004.Form, xep_0004.FormField, iterable=True)
        register_stanza_plugin(xep_0004.FormField, xep_0004.FieldOption, iterable=True)

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

        fields = OrderedDict()
        fields['f1'] = {'type': 'text-single',
                        'label': 'Username',
                        'required': True}
        fields['f2'] = {'type': 'text-private',
                        'label': 'Password',
                        'required': True}
        fields['f3'] = {'type': 'text-multi',
                        'label': 'Message',
                        'value': 'Enter message.\nA long one even.'}
        fields['f4'] = {'type': 'list-single',
                        'label': 'Message Type',
                        'options': [{'label': 'Cool!',
                                     'value': 'cool'},
                                    {'label': 'Urgh!',
                                     'value': 'urgh'}]}
        form.set_fields(fields)


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
        form.add_field(var='foo', ftype='text-single')
        form.add_field(var='bar', ftype='list-multi')

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

    def testSubmitType(self):
        """Test that setting type to 'submit' clears extra details"""
        msg = self.Message()
        form = msg['form']

        fields = OrderedDict()
        fields['f1'] = {'type': 'text-single',
                        'label': 'Username',
                        'required': True}
        fields['f2'] = {'type': 'text-private',
                        'label': 'Password',
                        'required': True}
        fields['f3'] = {'type': 'text-multi',
                        'label': 'Message',
                        'value': 'Enter message.\nA long one even.'}
        fields['f4'] = {'type': 'list-single',
                        'label': 'Message Type',
                        'options': [{'label': 'Cool!',
                                     'value': 'cool'},
                                    {'label': 'Urgh!',
                                     'value': 'urgh'}]}
        form.set_fields(fields)

        form['type'] = 'submit'
        form.set_values({'f1': 'username',
                          'f2': 'hunter2',
                          'f3': 'A long\nmultiline\nmessage',
                          'f4': 'cool'})

        self.check(form, """
          <x xmlns="jabber:x:data" type="submit">
            <field var="f1">
              <value>username</value>
            </field>
            <field var="f2">
              <value>hunter2</value>
            </field>
            <field var="f3">
              <value>A long</value>
              <value>multiline</value>
              <value>message</value>
            </field>
            <field var="f4">
              <value>cool</value>
            </field>
          </x>
        """, use_values=False)

    def testCancelType(self):
        """Test that setting type to 'cancel' clears all fields"""
        msg = self.Message()
        form = msg['form']

        fields = OrderedDict()
        fields['f1'] = {'type': 'text-single',
                        'label': 'Username',
                        'required': True}
        fields['f2'] = {'type': 'text-private',
                        'label': 'Password',
                        'required': True}
        fields['f3'] = {'type': 'text-multi',
                        'label': 'Message',
                        'value': 'Enter message.\nA long one even.'}
        fields['f4'] = {'type': 'list-single',
                        'label': 'Message Type',
                        'options': [{'label': 'Cool!',
                                     'value': 'cool'},
                                    {'label': 'Urgh!',
                                     'value': 'urgh'}]}
        form.set_fields(fields)

        form['type'] = 'cancel'

        self.check(form, """
          <x xmlns="jabber:x:data" type="cancel" />
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestDataForms)
