"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Dalek
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

import sleekxmpp
from sleekxmpp import Message
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.plugins.xep_0249 import Invite


log = logging.getLogger(__name__)


class xep_0249(base_plugin):

    """
    XEP-0249: Direct MUC Invitations
    """

    def plugin_init(self):
        self.xep = "0249"
        self.description = "Direct MUC Invitations"
        self.stanza = sleekxmpp.plugins.xep_0249.stanza

        self.xmpp.register_handler(
                Callback('Direct MUC Invitations',
                         StanzaPath('message/groupchat_invite'),
                         self._handle_invite))

        register_stanza_plugin(Message, Invite)

    def post_init(self):
        base_plugin.post_init(self)
        self.xmpp['xep_0030'].add_feature(Invite.namespace)

    def _handle_invite(self, msg):
        """
        Raise an event for all invitations received.
        """
        log.debug("Received direct muc invitation from %s to room %s",
                  msg['from'], msg['groupchat_invite']['jid'])

        self.xmpp.event('groupchat_direct_invite', msg)

    def send_invitation(self, jid, roomjid, password=None,
                        reason=None, ifrom=None):
        """
        Send a direct MUC invitation to an XMPP entity.

        Arguments:
            jid      -- The JID of the entity that will receive
                        the invitation
            roomjid  -- the address of the groupchat room to be joined
            password -- a password needed for entry into a
                        password-protected room (OPTIONAL).
            reason   -- a human-readable purpose for the invitation
                        (OPTIONAL).
        """

        msg = self.xmpp.Message()
        msg['to'] = jid
        if ifrom is not None:
            msg['from'] = ifrom
        msg['groupchat_invite']['jid'] = roomjid
        if password is not None:
            msg['groupchat_invite']['password'] = password
        if reason is not None:
            msg['groupchat_invite']['reason'] = reason

        return msg.send()
