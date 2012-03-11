"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.stanza.message import Message
from sleekxmpp.stanza.presence import Presence
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import MatchXPath
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.plugins.xep_0172 import stanza, UserNick


log = logging.getLogger(__name__)


class xep_0172(base_plugin):

    """
    XEP-0172: User Nickname
    """

    def plugin_init(self):
        self.xep = '0172'
        self.description = 'User Nickname'
        self.stanza = stanza

    def post_init(self):
        base_plugin.post_init(self)

        pubsub_stanza = self.xmpp['xep_0060'].stanza
        register_stanza_plugin(Message, UserNick)
        register_stanza_plugin(Presence, UserNick)
        register_stanza_plugin(pubsub_stanza.EventItem, UserNick)

        self.xmpp['xep_0030'].add_feature(UserNick.namespace)
        self.xmpp['xep_0163'].add_interest(UserNick.namespace)
        self.xmpp['xep_0060'].map_node_event(UserNick.namespace, 'user_nick')

    def publish_nick(self, nick=None, options=None, ifrom=None, block=True,
                     callback=None, timeout=None):
        """
        Publish the user's current nick.

        Arguments:
            nick     -- The user nickname to publish.
            options  -- Optional form of publish options.
            ifrom    -- Specify the sender's JID.
            block    -- Specify if the send call will block until a response
                        is received, or a timeout occurs. Defaults to True.
            timeout  -- The length of time (in seconds) to wait for a response
                        before exiting the send call if blocking is used.
                        Defaults to sleekxmpp.xmlstream.RESPONSE_TIMEOUT
            callback -- Optional reference to a stream handler function. Will
                        be executed when a reply stanza is received.
        """
        nickname = UserNick()
        nickname['nick'] = nick
        self.xmpp['xep_0163'].publish(nickname,
                node=UserNick.namespace,
                options=options,
                ifrom=ifrom,
                block=block,
                callback=callback,
                timeout=timeout)

    def stop(self, ifrom=None, block=True, callback=None, timeout=None):
        """
        Clear existing user nick information to stop notifications.

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
        nick = UserNick()
        self.xmpp['xep_0163'].publish(nick, 
                node=UserNick.namespace,
                ifrom=ifrom,
                block=block,
                callback=callback,
                timeout=timeout)
