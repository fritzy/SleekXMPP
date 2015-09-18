
from sleekxmpp.xmlstream import ElementBase, ET


class FormValidation(ElementBase):
    """
    Validation values for form fields.

    Example:

    <field var='evt.date' type='text-single' label='Event Date/Time'>
      <validate xmlns='http://jabber.org/protocol/xdata-validate'
                datatype='xs:dateTime'/>
      <value>2003-10-06T11:22:00-07:00</value>
    </field>

    Questions:
      Should this look at the datatype value and convert the range values as appropriate?
      Should this stanza provide a pass/fail for a value from the field, or convert field value to datatype?
    """

    namespace = 'http://jabber.org/protocol/xdata-validate'
    name = 'validate'
    plugin_attrib = 'validate'
    interfaces = {'datatype', 'basic', 'open', 'range', 'regex', }
    sub_interfaces = {'basic', 'open', 'range', 'regex', }
    plugin_attrib_map = {}
    plugin_tag_map = {}

    def _add_field(self, name):
        self.remove_all()
        item_xml = ET.Element('{%s}%s' % (self.namespace, name))
        self.xml.append(item_xml)
        return item_xml

    def set_basic(self, value):
        if value:
            self._add_field('basic')
        else:
            del self['basic']

    def set_open(self, value):
        if value:
            self._add_field('open')
        else:
            del self['open']

    def set_regex(self, regex):
        if regex:
            _regex = self._add_field('regex')
            _regex.text = regex
        else:
            del self['regex']

    def set_range(self, value, minimum=None, maximum=None):
        if value:
            _range = self._add_field('range')
            _range.attrib['min'] = str(minimum)
            _range.attrib['max'] = str(maximum)
        else:
            del self['range']

    def remove_all(self, except_tag=None):
        for a in self.sub_interfaces:
            if a != except_tag:
                del self[a]

    def get_basic(self):
        present = self.xml.find('{%s}basic' % self.namespace)
        return present is not None

    def get_open(self):
        present = self.xml.find('{%s}open' % self.namespace)
        return present is not None

    def get_regex(self):
        present = self.xml.find('{%s}regex' % self.namespace)
        if present is not None:
            return present.text

        return False

    def get_range(self):
        present = self.xml.find('{%s}range' % self.namespace)
        if present is not None:
            attributes = present.attrib
            return_value = dict()
            if 'min' in attributes:
                return_value['minimum'] = attributes['min']
            if 'max' in attributes:
                return_value['maximum'] = attributes['max']
            return return_value

        return False
