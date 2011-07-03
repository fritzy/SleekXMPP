"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""


from sleekxmpp.stanza import Message, Presence, Iq
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.plugins.xep_0066 import stanza


class xep_0066(base_plugin):

    """
    XEP-0066: Out-of-Band Data

    Out-of-Band Data is a basic method for transferring files between
    XMPP agents. The URL of the resource in question is sent to the receiving
    entity, which then downloads the resource before responding to the OOB
    request. OOB is also used as a generic means to transmit URLs in other
    stanzas to indicate where to find additional information.

    Also see <http://www.xmpp.org/extensions/xep-0066.html>.

    Events:
        oob_transfer -- Raised when a request to download a resource
                        has been received.

    Methods:
        send_oob -- Send a request to another entity to download a file
                    or other addressable resource.
    """

    def plugin_init(self):
        """Start the XEP-0066 plugin."""
        self.xep = '0066'
        self.description = 'Out-of-Band Transfer'
        self.stanza = stanza

        register_stanza_plugin(Iq, stanza.OOBTransfer)
        register_stanza_plugin(Message, stanza.OOB)
        register_stanza_plugin(Presence, stanza.OOB)

        self.xmpp.register_handler(
                Callback('OOB Transfer',
                         StanzaPath('iq@type=set/oob_transfer'),
                         self._handle_transfer))

    def post_init(self):
        """Handle cross-plugin dependencies."""
        base_plugin.post_init(self)
        self.xmpp['xep_0030'].add_feature(stanza.OOBTransfer.namespace)
        self.xmpp['xep_0030'].add_feature(stanza.OOB.namespace)

    def send_oob(self, to, url, desc=None, ifrom=None, **iqargs):
        """
        Initiate a basic file transfer by sending the URL of
        a file or other resource.

        Arguments:
            url      -- The URL of the resource to transfer.
            desc     -- An optional human readable description of the item
                        that is to be transferred.
            ifrom    -- Specifiy the sender's JID.
            block    -- If true, block and wait for the stanzas' reply.
            timeout  -- The time in seconds to block while waiting for
                        a reply. If None, then wait indefinitely.
            callback -- Optional callback to execute when a reply is
                        received instead of blocking and waiting for
                        the reply.
        """
        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['to'] = to
        if ifrom:
            iq['from'] = ifrom
        iq['oob_transfer']['url'] = url
        iq['oob_transfer']['desc'] = desc
        return iq.send(**iqargs)

    def _handle_transfer(self, iq):
        """Handle receiving an out-of-band transfer request."""
        self.xmpp.event('oob_transfer', iq)
