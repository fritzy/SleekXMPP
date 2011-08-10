"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import StreamFeatures
from sleekxmpp.xmlstream import ElementBase, StanzaBase, ET
from sleekxmpp.xmlstream import register_stanza_plugin


class Success(StanzaBase):

    """
    """

    name = 'success'
    namespace = 'urn:ietf:params:xml:ns:xmpp-sasl'
    interfaces = set()
    plugin_attrib = name

    def setup(self, xml):
        StanzaBase.setup(self, xml)
        self.xml.tag = self.tag_name()
