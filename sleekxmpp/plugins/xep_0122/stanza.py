
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
    """

    namespace = 'http://jabber.org/protocol/xdata-validate'
    name = 'validate'
    plugin_attrib = 'validate'
    interfaces = set(('datatype', 'basic', 'open', 'range', 'regex', ))
    sub_interfaces = set(('basic', 'open', 'range', 'regex', ))
    plugin_attrib_map = {}
    plugin_tag_map = {}

    def _add_field(self, name):
        item_xml = ET.Element('{%s}%s' % (self.namespace, name))
        self.xml.append(item_xml)
        return item_xml

    def set_basic(self, value):
        self.remove_all()
        if value:
            self._add_field('basic')

    def set_open(self, value):
        self.remove_all()
        if value:
            self._add_field('open')

    def set_regex(self, regex):
        self.remove_all()
        if regex:
            _regex = self._add_field('regex')
            _regex.text = regex

    def set_range(self, value, minimum=None, maximum=None):
        self.remove_all()
        if value:
            _range = self._add_field('range')
            _range.attrib['min'] = str(minimum)
            _range.attrib['max'] = str(maximum)

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
        if present:
            return present.text

        return False

    def get_range(self):
        present = self.xml.find('{%s}regex' % self.namespace)
        if present:
            return dict(present.attrib)

        return False


FormValidation.getBasic = FormValidation.get_basic
FormValidation.setBasic = FormValidation.set_basic
