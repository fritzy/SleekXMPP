"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ElementBase


class Forwarded(ElementBase):
    name = 'forwarded'
    namespace = 'urn:xmpp:forward:0'
    plugin_attrib = 'forwarded'
    interfaces = set(['stanza'])

    def get_stanza(self):
        if self.xml.find('{jabber:client}message') is not None:
            return self['message']
        elif self.xml.find('{jabber:client}presence') is not None:
            return self['presence']
        elif self.xml.find('{jabber:client}iq') is not None:
            return self['iq']
        return ''

    def set_stanza(self, value):
        self.del_stanza()
        self.append(value)

    def del_stanza(self):
        del self['message']
        del self['presence']
        del self['iq']
