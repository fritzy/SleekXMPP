import unittest

from sleekxmpp import Message
from sleekxmpp.test import SleekTest
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
        """Testing basic validation setting and getting."""
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

        self.assertTrue(validation.get_basic())
        self.assertFalse(validation.get_open())
        self.assertFalse(validation.get_range())
        self.assertFalse(validation.get_regex())

    def test_open_validation(self):
        """Testing open validation setting and getting."""
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
                    <open />
                </validate>
              </field>
            </x>
          </message>
        """)

        self.assertFalse(validation.get_basic())
        self.assertTrue(validation.get_open())
        self.assertFalse(validation.get_range())
        self.assertFalse(validation.get_regex())

    def test_regex_validation(self):
        """Testing regex validation setting and getting."""
        msg = self.Message()
        form = msg['form']
        field = form.addField(var='f1',
                              ftype='text-single',
                              label='Text',
                              desc='A text field',
                              required=True,
                              value='Some text!')

        regex_value = '[0-9]+'

        validation = field['validate']
        validation.set_regex(regex_value)

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

        self.assertFalse(validation.get_basic())
        self.assertFalse(validation.get_open())
        self.assertFalse(validation.get_range())
        self.assertTrue(validation.get_regex())

        self.assertEqual(regex_value, validation.get_regex())

    def test_range_validation(self):
        """Testing range validation setting and getting."""
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

        self.assertDictEqual(dict(minimum=str(0), maximum=str(10)), validation.get_range())

    def test_reported_field_validation(self):
        """
        Testing adding validation to the field when it's stored in the reported.
        :return:
        """
        msg = self.Message()
        form = msg['form']
        field = form.addReported(var='f1', ftype='text-single', label='Text')
        validation = field['validate']
        validation.set_basic(True)

        form.addItem({'f1': 'Some text!'})

        self.check(msg, """
          <message>
            <x xmlns="jabber:x:data" type="form">
              <reported>
                <field var="f1" type="text-single" label="Text">
                  <validate xmlns="http://jabber.org/protocol/xdata-validate">
                    <basic />
                  </validate>
                </field>
              </reported>
              <item>
                <field var="f1">
                  <value>Some text!</value>
                </field>
              </item>
            </x>
          </message>
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestDataForms)
