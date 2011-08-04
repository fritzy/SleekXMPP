"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import base64

from sleekxmpp.thirdparty.suelta.util import bytes

from sleekxmpp.stanza import StreamFeatures
from sleekxmpp.xmlstream import ElementBase, StanzaBase, ET
from sleekxmpp.xmlstream import register_stanza_plugin


class Response(StanzaBase):

    """
    """

    name = 'response'
    namespace = 'urn:ietf:params:xml:ns:xmpp-sasl'
    interfaces = set(('value',))
    plugin_attrib = name

    def setup(self, xml):
        StanzaBase.setup(self, xml)
        self.xml.tag = self.tag_name()

    def get_value(self):
        return base64.b64decode(bytes(self.xml.text))

    def set_value(self, values):
        self.xml.text = bytes(base64.b64encode(values)).decode('utf-8')

    def del_value(self):
        self.xml.text = ''
