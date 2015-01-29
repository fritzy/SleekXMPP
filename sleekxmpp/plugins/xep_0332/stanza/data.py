"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of HTTP over XMPP transport
    http://xmpp.org/extensions/xep-0332.html
    Copyright (C) 2015 Riptide IO, sangeeth@riptideio.com
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ElementBase


class Data(ElementBase):
    """
    The data element.
    """
    name = 'data'
    namespace = ''
    interfaces = set(['data'])
    plugin_attrib = 'data'

    def get_data(self):
        print "Data:: get_data()"

    def set_data(self, data, encoding='text'):
        print "Data:: set_data()"
        self._set_sub_text(encoding, text=data)

