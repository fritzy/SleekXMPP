"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2016 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import Error
from sleekxmpp.xmlstream import ElementBase, StanzaBase

class ClientStateIndication(ElementBase):
    name = 'csi'
    namespace = 'urn:xmpp:csi:0'
    plugin_attrib = name

class Active(StanzaBase):
    name = 'active'
    plugin_attrib = 'active'
    namespace = 'urn:xmpp:csi:0'

    def setup(self, xml):
        StanzaBase.setup(self, xml)
        self.xml.tag = self.tag_name()

class Inactive (StanzaBase):
    name = 'inactive'
    plugin_attrib = 'inactive'
    namespace = 'urn:xmpp:csi:0'

    def setup(self, xml):
        StanzaBase.setup(self, xml)
        self.xml.tag = self.tag_name()
