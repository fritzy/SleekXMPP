"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2016 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp import Message
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins.xep_0334 import stanza, Store, NoStore, NoPermanentStore, NoCopy

log = logging.getLogger(__name__)

class XEP_0334(BasePlugin):

    name = 'xep_0334'
    description = 'XEP-0334: Message Processing Hints'
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Message, Store)
        register_stanza_plugin(Message, NoStore)
        register_stanza_plugin(Message, NoPermanentStore)
        register_stanza_plugin(Message, NoCopy)
