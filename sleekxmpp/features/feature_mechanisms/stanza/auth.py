"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import StreamFeatures
from sleekxmpp.xmlstream import ElementBase, StanzaBase, ET
from sleekxmpp.xmlstream import register_stanza_plugin


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
