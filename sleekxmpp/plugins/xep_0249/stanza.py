"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Dalek
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.jid import JID
from sleekxmpp.xmlstream import ElementBase


class Invite(ElementBase):

    """
    XMPP allows for an agent in an MUC room to directly invite another
    user to join the chat room (as opposed to a mediated invitation
    done through the server).

    Example invite stanza:
      <message from='crone1@shakespeare.lit/desktop'
          to='hecate@shakespeare.lit'>
        <x xmlns='jabber:x:conference'
           jid='darkcave@macbeth.shakespeare.lit'
           password='cauldronburn'
           reason='Hey Hecate, this is the place for all good witches!'/>
      </message>

    Stanza Interface:
        jid      -- The JID of the groupchat room
        password -- The password used to gain entry in the room
                    (optional)
        reason   -- The reason for the invitation (optional)

    """

    name = 'x'
    namespace = 'jabber:x:conference'
    plugin_attrib = 'groupchat_invite'
    interfaces = set(['jid', 'password', 'reason', 'continue', 'thread'])

    def get_continue(self):
        return self._get_attr('continue', '') in ('true', '1')

    def set_continue(self, value):
        if value:
            self._set_attr('continue', 'true')
        else:
            self._del_attr('continue')

    def get_jid(self):
        return JID(self._get_attr('jid'))

    def set_jid(self, value):
        return self._set_attr('jid', str(value))
