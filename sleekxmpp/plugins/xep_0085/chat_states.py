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
from sleekxmpp.plugins.base import BasePlugin, register_plugin
from sleekxmpp.plugins.xep_0085 import stanza, ChatState


log = logging.getLogger(__name__)


class XEP_0085(BasePlugin):

    """
    XEP-0085 Chat State Notifications
    """

    name = 'xep_0085'
    description = 'XEP-0085: Chat State Notifications'
    dependencies = set(['xep_0030'])
    stanza = stanza

    def plugin_init(self):
        for state in ChatState.states:
            self.xmpp.register_handler(
                Callback('Chat State: %s' % state,
                         StanzaPath('message@chat_state=%s' % state),
                         self._handle_chat_state))

        register_stanza_plugin(Message, ChatState)

        self.xmpp.plugin['xep_0030'].add_feature(ChatState.namespace)

    def _handle_chat_state(self, msg):
        state = msg['chat_state']
        log.debug("Chat State: %s, %s", state, msg['from'].jid)
        self.xmpp.event('chatstate_%s' % state, msg)


register_plugin(XEP_0085)
