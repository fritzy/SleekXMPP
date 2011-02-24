"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permissio
"""

import logging

import sleekxmpp
from sleekxmpp.stanza import Message
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.xmlstream import register_stanza_plugin, ElementBase, ET
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.plugins.xep_0085 import stanza


log = logging.getLogger(__name__)


class xep_0085(base_plugin):

    """
    XEP-0085 Chat State Notifications
    """

    def plugin_init(self):
        self.xep = '0085'
        self.description = 'Chat State Notifications'
        self.stanza = stanza

        self.xmpp.registerHandler(
            Callback('Chat States',
                     StanzaPath('message/chat_state'),
                     self._handle_chat_state))

        register_stanza_plugin(Message, stanza.ChatState)

    def post_init(self):
        base_plugin.post_init(self)
        self.xmpp.plugin['xep_0030'].add_feature(stanza.ChatState.namepsace)

    def _handle_chat_state(self, msg):
        state = msg['chat_state']
        log.debug("Chat State: %s, %s" % (state, msg['from'].jid))
        self.xmpp.event('chatstate_%s' % state, msg)
