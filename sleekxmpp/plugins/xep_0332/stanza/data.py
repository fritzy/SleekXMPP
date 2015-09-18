"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of HTTP over XMPP transport
    http://xmpp.org/extensions/xep-0332.html
    Copyright (C) 2015 Riptide IO, sangeeth@riptideio.com
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ElementBase


class HTTPData(ElementBase):
    """
    The data element.
    """
    name = 'data'
    namespace = 'urn:xmpp:http'
    interfaces = set(['data'])
    plugin_attrib = 'data'
    is_extension = True

    def get_data(self, encoding='text'):
        data = self._get_sub_text(encoding, None)
        return str(data) if data is not None else data

    def set_data(self, data, encoding='text'):
        self._set_sub_text(encoding, text=data)

