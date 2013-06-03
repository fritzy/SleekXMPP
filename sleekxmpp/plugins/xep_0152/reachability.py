"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.plugins.base import BasePlugin
from sleekxmpp.plugins.xep_0152 import stanza, Reachability


log = logging.getLogger(__name__)


class XEP_0152(BasePlugin):

    """
    XEP-0152: Reachability Addresses
    """

    name = 'xep_0152'
    description = 'XEP-0152: Reachability Addresses'
    dependencies = set(['xep_0163'])
    stanza = stanza

    def plugin_end(self):
        self.xmpp['xep_0030'].del_feature(feature=Reachability.namespace)
        self.xmpp['xep_0163'].remove_interest(Reachability.namespace)

    def session_bind(self, jid):
        self.xmpp['xep_0163'].register_pep('reachability', Reachability)

    def publish_reachability(self, addresses, options=None,
                        ifrom=None, block=True, callback=None, timeout=None):
        """
        Publish alternative addresses where the user can be reached.

        Arguments:
            addresses -- A list of dictionaries containing the URI and
                         optional description for each address.
            options   -- Optional form of publish options.
            ifrom     -- Specify the sender's JID.
            block     -- Specify if the send call will block until a response
                         is received, or a timeout occurs. Defaults to True.
            timeout   -- The length of time (in seconds) to wait for a response
                         before exiting the send call if blocking is used.
                         Defaults to sleekxmpp.xmlstream.RESPONSE_TIMEOUT
            callback  -- Optional reference to a stream handler function. Will
                         be executed when a reply stanza is received.
        """
        if not isinstance(addresses, (list, tuple)):
            addresses = [addresses]
        reach = Reachability()
        for address in addresses:
            if not hasattr(address, 'items'):
                address = {'uri': address}

            addr = stanza.Address()
            for key, val in address.items():
                addr[key] = val
            reach.append(addr)
        return self.xmpp['xep_0163'].publish(reach,
                node=Reachability.namespace,
                options=options,
                ifrom=ifrom,
                block=block,
                callback=callback,
                timeout=timeout)

    def stop(self, ifrom=None, block=True, callback=None, timeout=None):
        """
        Clear existing user activity information to stop notifications.

        Arguments:
            ifrom    -- Specify the sender's JID.
            block    -- Specify if the send call will block until a response
                        is received, or a timeout occurs. Defaults to True.
            timeout  -- The length of time (in seconds) to wait for a response
                        before exiting the send call if blocking is used.
                        Defaults to sleekxmpp.xmlstream.RESPONSE_TIMEOUT
            callback -- Optional reference to a stream handler function. Will
                        be executed when a reply stanza is received.
        """
        reach = Reachability()
        return self.xmpp['xep_0163'].publish(reach,
                node=Reachability.namespace,
                ifrom=ifrom,
                block=block,
                callback=callback,
                timeout=timeout)
