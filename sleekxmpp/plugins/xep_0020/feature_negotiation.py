"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp import Iq, Message
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.xmlstream import register_stanza_plugin, JID
from sleekxmpp.plugins.xep_0020 import stanza, FeatureNegotiation
from sleekxmpp.plugins.xep_0004 import Form


log = logging.getLogger(__name__)


class XEP_0020(BasePlugin):

    name = 'xep_0020'
    description = 'XEP-0020: Feature Negotiation'
    dependencies = set(['xep_0004', 'xep_0030'])
    stanza = stanza

    def plugin_init(self):
        self.xmpp['xep_0030'].add_feature(FeatureNegotiation.namespace)

        register_stanza_plugin(FeatureNegotiation, Form)

        register_stanza_plugin(Iq, FeatureNegotiation)
        register_stanza_plugin(Message, FeatureNegotiation)
