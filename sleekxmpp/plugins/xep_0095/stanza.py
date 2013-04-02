"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ElementBase


class SI(ElementBase):
    name = 'si'
    namespace = 'http://jabber.org/protocol/si'
    plugin_attrib = 'si'
    interfaces = set(['id', 'mime_type', 'profile'])

    def get_mime_type(self):
        return self._get_attr('mime-type', 'application/octet-stream')

    def set_mime_type(self, value):
        self._set_attr('mime-type', value)

    def del_mime_type(self):
        self._del_attr('mime-type')
