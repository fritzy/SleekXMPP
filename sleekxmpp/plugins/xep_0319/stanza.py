"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import datetime as dt

from sleekxmpp.xmlstream import ElementBase
from sleekxmpp.plugins import xep_0082


class Idle(ElementBase):
    name = 'idle'
    namespace = 'urn:xmpp:idle:1'
    plugin_attrib = 'idle'
    interfaces = set(['since'])

    def get_since(self):
        timestamp = self._get_attr('since')
        return xep_0082.parse(timestamp)

    def set_since(self, value):
        if isinstance(value, dt.datetime):
            value = xep_0082.format_datetime(value)
        self._set_attr('since', value)
