"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.plugins.base import BasePlugin
from sleekxmpp.plugins.xep_0196 import stanza, UserGaming


log = logging.getLogger(__name__)


class XEP_0196(BasePlugin):

    """
    XEP-0196: User Gaming
    """

    name = 'xep_0196'
    description = 'XEP-0196: User Gaming'
    dependencies = set(['xep_0163'])
    stanza = stanza

    def plugin_end(self):
        self.xmpp['xep_0030'].del_feature(feature=UserGaming.namespace)
        self.xmpp['xep_0163'].remove_interest(UserGaming.namespace)

    def session_bind(self, jid):
        self.xmpp['xep_0163'].register_pep('user_gaming', UserGaming)

    def publish_gaming(self, name=None, level=None, server_name=None, uri=None,
                    character_name=None, character_profile=None, server_address=None,
                    options=None, ifrom=None, block=True, callback=None, timeout=None):
        """
        Publish the user's current gaming status.

        Arguments:
            name              -- The name of the game.
            level             -- The user's level in the game.
            uri               -- A URI for the game or relevant gaming service
            server_name       -- The name of the server where the user is playing.
            server_address    -- The hostname or IP address of the server where the
                                 user is playing.
            character_name    -- The name of the user's character in the game.
            character_profile -- A URI for a profile of the user's character.
            options           -- Optional form of publish options.
            ifrom             -- Specify the sender's JID.
            block             -- Specify if the send call will block until a response
                                 is received, or a timeout occurs. Defaults to True.
            timeout           -- The length of time (in seconds) to wait for a response
                                 before exiting the send call if blocking is used.
                                 Defaults to sleekxmpp.xmlstream.RESPONSE_TIMEOUT
            callback          -- Optional reference to a stream handler function. Will
                                 be executed when a reply stanza is received.
        """
        gaming = UserGaming()
        gaming['name'] = name
        gaming['level'] = level
        gaming['uri'] = uri
        gaming['character_name'] = character_name
        gaming['character_profile'] = character_profile
        gaming['server_name'] = server_name
        gaming['server_address'] = server_address
        return self.xmpp['xep_0163'].publish(gaming,
                node=UserGaming.namespace,
                options=options,
                ifrom=ifrom,
                block=block,
                callback=callback,
                timeout=timeout)

    def stop(self, ifrom=None, block=True, callback=None, timeout=None):
        """
        Clear existing user gaming information to stop notifications.

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
        gaming = UserGaming()
        return self.xmpp['xep_0163'].publish(gaming,
                node=UserGaming.namespace,
                ifrom=ifrom,
                block=block,
                callback=callback,
                timeout=timeout)
