"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""


from sleekxmpp.stanza import Message, Presence
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.plugins.xep_0203 import stanza


class xep_0203(base_plugin):

    """
    XEP-0203: Delayed Delivery

    XMPP stanzas are sometimes withheld for delivery due to the recipient
    being offline, or are resent in order to establish recent history as
    is the case with MUCS. In any case, it is important to know when the
    stanza was originally sent, not just when it was last received.

    Also see <http://www.xmpp.org/extensions/xep-0203.html>.
    """

    def plugin_init(self):
        """Start the XEP-0203 plugin."""
        self.xep = '0203'
        self.description = 'Delayed Delivery'
        self.stanza = stanza

        register_stanza_plugin(Message, stanza.Delay)
        register_stanza_plugin(Presence, stanza.Delay)
