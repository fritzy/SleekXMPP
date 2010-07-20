"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging
from . import base
from .. xmlstream.handler.callback import Callback
from .. xmlstream.matcher.xpath import MatchXPath
from .. xmlstream.stanzabase import registerStanzaPlugin, ElementBase, ET, JID
from .. stanza.iq import Iq
from . xep_0030 import DiscoInfo, DiscoItems
from . xep_0004 import Form


class xep_0128(base.base_plugin):
    """
    XEP-0128 Service Discovery Extensions
    """
	
    def plugin_init(self):
        self.xep = '0128'
        self.description = 'Service Discovery Extensions'

        registerStanzaPlugin(DiscoInfo, Form)
        registerStanzaPlugin(DiscoItems, Form)

    def extend_info(self, node, data=None):
        if data is None:
            data = {}
        node = self.xmpp['xep_0030'].nodes.get(node, None)
        if node is None:
            self.xmpp['xep_0030'].add_node(node)
        
        info = node.info
        info['form']['type'] = 'result'
        info['form'].setFields(data, default=None)

    def extend_items(self, node, data=None):
        if data is None:
            data = {}
        node = self.xmpp['xep_0030'].nodes.get(node, None)
        if node is None:
            self.xmpp['xep_0030'].add_node(node)
        
        items = node.items
        items['form']['type'] = 'result'
        items['form'].setFields(data, default=None)
