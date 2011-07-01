"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import StreamFeatures
from sleekxmpp.xmlstream import ElementBase, StanzaBase, ET
from sleekxmpp.xmlstream import register_stanza_plugin


class Mechanisms(ElementBase):

    """
    """

    name = 'mechanisms'
    namespace = 'urn:ietf:params:xml:ns:xmpp-sasl'
    interfaces = set(('mechanisms', 'required'))
    plugin_attrib = name
    is_extension = True

    def get_required(self):
        """
        """
        return True

    def get_mechanisms(self):
        """
        """
        results = []
        mechs = self.findall('{%s}mechanism' % self.namespace)
        if mechs:
            for mech in mechs:
                results.append(mech.text)
        return results

    def set_mechanisms(self, values):
        """
        """
        self.del_mechanisms()
        for val in values:
           mech = ET.Element('{%s}mechanism' % self.namespace)
           mech.text = val
           self.append(mech)

    def del_mechanisms(self):
        """
        """
        mechs = self.findall('{%s}mechanism' % self.namespace)
        if mechs:
            for mech in mechs:
                self.xml.remove(mech)


class Success(StanzaBase):

    """
    """

    name = 'success'
    namespace = 'urn:ietf:params:xml:ns:xmpp-sasl'
    interfaces = set()
    plugin_attrib = name


class Failure(StanzaBase):

    """
    """

    name = 'failure'
    namespace = 'urn:ietf:params:xml:ns:xmpp-sasl'
    interfaces = set()
    plugin_attrib = name


class Auth(StanzaBase):

    """
    """

    name = 'auth'
    namespace = 'urn:ietf:params:xml:ns:xmpp-sasl'
    interfaces = set(('mechanism', 'value'))
    plugin_attrib = name

    def setup(self, xml):
        StanzaBase.setup(self, xml)
        self.xml.tag = self.tag_name()

    def set_value(self, value):
        self.xml.text = value

    def get_value(self):
        return self.xml.text

    def del_value(self):
        self.xml.text = ''


register_stanza_plugin(StreamFeatures, Mechanisms)
