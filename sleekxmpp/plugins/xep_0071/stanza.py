"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import Message
from sleekxmpp.util import unicode
from sleekxmpp.thirdparty import OrderedDict
from sleekxmpp.xmlstream import ElementBase, ET, register_stanza_plugin, tostring


XHTML_NS = 'http://www.w3.org/1999/xhtml'


class XHTML_IM(ElementBase):

    namespace = 'http://jabber.org/protocol/xhtml-im'
    name = 'html'
    interfaces = set(['body'])
    lang_interfaces = set(['body'])
    plugin_attrib = name

    def set_body(self, content, lang=None):
        if lang is None:
            lang = self.get_lang()
        self.del_body(lang)
        if lang == '*':
            for sublang, subcontent in content.items():
                self.set_body(subcontent, sublang)
        else:
            if isinstance(content, type(ET.Element('test'))):
                content = unicode(ET.tostring(content))
            else:
                content = unicode(content)
            header = '<body xmlns="%s"' % XHTML_NS
            if lang:
                header = '%s xml:lang="%s"' % (header, lang)
            content = '%s>%s</body>' % (header, content)
            xhtml = ET.fromstring(content)
            self.xml.append(xhtml)

    def get_body(self, lang=None):
        """Return the contents of the HTML body."""
        if lang is None:
            lang = self.get_lang()

        bodies = self.xml.findall('{%s}body' % XHTML_NS)

        if lang == '*':
            result = OrderedDict()
            for body in bodies:
                body_lang = body.attrib.get('{%s}lang' % self.xml_ns, '')
                body_result = []
                body_result.append(body.text if body.text else '')
                for child in body:
                    body_result.append(tostring(child, xmlns=XHTML_NS))
                body_result.append(body.tail if body.tail else '')
                result[body_lang] = ''.join(body_result)
            return result
        else:
            for body in bodies:
                if body.attrib.get('{%s}lang' % self.xml_ns, self.get_lang()) == lang:
                    result = []
                    result.append(body.text if body.text else '')
                    for child in body:
                        result.append(tostring(child, xmlns=XHTML_NS))
                    result.append(body.tail if body.tail else '')
                    return ''.join(result)
        return ''

    def del_body(self, lang=None):
        if lang is None:
            lang = self.get_lang()
        bodies = self.xml.findall('{%s}body' % XHTML_NS)
        for body in bodies:
            if body.attrib.get('{%s}lang' % self.xml_ns, self.get_lang()) == lang:
                self.xml.remove(body)
                return
