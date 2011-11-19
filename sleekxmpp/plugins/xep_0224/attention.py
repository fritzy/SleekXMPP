"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.stanza import Message
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.plugins.xep_0224 import stanza


log = logging.getLogger(__name__)


class xep_0224(base_plugin):

    """
    XEP-0224: Attention
    """

    def plugin_init(self):
        """Start the XEP-0224 plugin."""
        self.xep = '0224'
        self.description = 'Attention'
        self.stanza = stanza

        register_stanza_plugin(Message, stanza.Attention)

        self.xmpp.register_handler(
                Callback('Attention',
                    StanzaPath('message/attention'),
                    self._handle_attention))

    def post_init(self):
        """Handle cross-plugin dependencies."""
        base_plugin.post_init(self)
        self.xmpp['xep_0030'].add_feature(stanza.Attention.namespace)

    def request_attention(self, to, mfrom=None, mbody=''):
        """
        Send an attention message with an optional body.

        Arguments:
            to    -- The attention request recipient's JID.
            mfrom -- Optionally specify the sender of the attention request.
            mbody -- An optional message body to include in the request.
        """
        m = self.xmpp.Message()
        m['to'] = to
        m['type'] = 'headline'
        m['attention'] = True
        if mfrom:
            m['from'] = mfrom
        m['body'] = mbody
        m.send()

    def _handle_attention(self, msg):
        """
        Raise an event after receiving a message with an attention request.

        Arguments:
            msg -- A message stanza with an attention element.
        """
        log.debug("Received attention request from: %s", msg['from'])
        self.xmpp.event('attention', msg)
