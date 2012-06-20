"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp import Message, Presence
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.plugins.xep_0033 import stanza, Addresses


class XEP_0033(BasePlugin):

    """
    XEP-0033: Extended Stanza Addressing
    """

    name = 'xep_0033'
    description = 'XEP-0033: Extended Stanza Addressing'
    dependencies = set(['xep_0030'])
    stanza = stanza

    def plugin_init(self):
        self.xmpp['xep_0030'].add_feature(Addresses.namespace)

        register_stanza_plugin(Message, Addresses)
        register_stanza_plugin(Presence, Addresses)
