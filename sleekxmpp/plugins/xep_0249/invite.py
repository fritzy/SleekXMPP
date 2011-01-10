"""Direct MUC Invitation."""


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
        self.xmpp.plugin['xep_0030'].add_feature(Invite.namespace)

    def _handle_invite(self, message):
        """
        Raise an event for all invitations received.

        """
        log.debug("Received direct muc invitation from %s to room %s",
                  message['from'], message['groupchat_invite']['jid'])

        self.xmpp.event('groupchat_direct_invite', message)

    def send_invitation(self, jid, roomjid, password=None,
                        reason=None, ifrom=None):
        """
        Send a direct MUC invitation to an XMPP entity.

        Arguments:
            jid         -- The jid of the entity to which the inviation
                           is sent
            roomjid     -- the address of the groupchat room to be joined
            password    -- a password needed for entry into a
                           password-protected room (OPTIONAL).
            reason      -- a human-readable purpose for the invitation
                           (OPTIONAL).

        """

        message = self.xmpp.Message()
        message['to'] = jid
        if ifrom is not None:
            message['from'] = ifrom
        message['groupchat_invite']['jid'] = roomjid
        if password is not None:
            message['groupchat_invite']['password'] = password
        if reason is not None:
            message['groupchat_invite']['reason'] = reason

        return message.send()
