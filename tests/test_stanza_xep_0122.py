import unittest
from sleekxmpp import Message
from sleekxmpp.test import SleekTest
from sleekxmpp.thirdparty import OrderedDict

import sleekxmpp.plugins.xep_0004 as xep_0004
import sleekxmpp.plugins.xep_0122 as xep_0122
from sleekxmpp.xmlstream import register_stanza_plugin


class TestDataForms(SleekTest):

    def setUp(self):
        register_stanza_plugin(Message, xep_0004.Form)
        register_stanza_plugin(xep_0004.Form, xep_0004.FormField, iterable=True)
        register_stanza_plugin(xep_0004.FormField, xep_0004.FieldOption, iterable=True)
        register_stanza_plugin(xep_0004.FormField, xep_0122.FormValidation)

    def test_basic_validation(self):
        """Testing using multiple instructions elements in a data form."""
        msg = self.Message()
        form = msg['form']
        field = form.addField(var='f1',
                              ftype='text-single',
                              label='Text',
                              desc='A text field',
                              required=True,
                              value='Some text!')

        validation = field['validate']
        validation['datatype'] = 'xs:string'
        validation.set_basic(True)

        self.check(msg, """
          <message>
            <x xmlns="jabber:x:data" type="form">
              <field var="f1" type="text-single" label="Text">
                <desc>A text field</desc>
                <required />
                <value>Some text!</value>
                <validate xmlns="http://jabber.org/protocol/xdata-validate" datatype="xs:string">
                    <basic/>
                </validate>
              </field>
            </x>
          </message>
        """)

    def test_open_validation(self):
        """Testing using multiple instructions elements in a data form."""
        msg = self.Message()
        form = msg['form']
        field = form.addField(var='f1',
                              ftype='text-single',
                              label='Text',
                              desc='A text field',
                              required=True,
                              value='Some text!')

        validation = field['validate']
        validation.set_open(True)

        self.check(msg, """
          <message>
            <x xmlns="jabber:x:data" type="form">
              <field var="f1" type="text-single" label="Text">
                <desc>A text field</desc>
                <required />
                <value>Some text!</value>
                <validate xmlns="http://jabber.org/protocol/xdata-validate">
                    <open/>
                </validate>
              </field>
            </x>
          </message>
        """)

    def test_regex_validation(self):
        """Testing using multiple instructions elements in a data form."""
        msg = self.Message()
        form = msg['form']
        field = form.addField(var='f1',
                              ftype='text-single',
                              label='Text',
                              desc='A text field',
                              required=True,
                              value='Some text!')

        validation = field['validate']
        validation.set_regex('[0-9]+')

        self.check(msg, """
          <message>
            <x xmlns="jabber:x:data" type="form">
              <field var="f1" type="text-single" label="Text">
                <desc>A text field</desc>
                <required />
                <value>Some text!</value>
                <validate xmlns="http://jabber.org/protocol/xdata-validate">
                    <regex>[0-9]+</regex>
                </validate>
              </field>
            </x>
          </message>
        """)

    def test_range_validation(self):
        """Testing using multiple instructions elements in a data form."""
        msg = self.Message()
        form = msg['form']
        field = form.addField(var='f1',
                              ftype='text-single',
                              label='Text',
                              desc='A text field',
                              required=True,
                              value='Some text!')

        validation = field['validate']
        validation.set_range(True, minimum=0, maximum=10)

        self.check(msg, """
          <message>
            <x xmlns="jabber:x:data" type="form">
              <field var="f1" type="text-single" label="Text">
                <desc>A text field</desc>
                <required />
                <value>Some text!</value>
                <validate xmlns="http://jabber.org/protocol/xdata-validate">
                    <range min="0" max="10" />
                </validate>
              </field>
            </x>
          </message>
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestDataForms)
