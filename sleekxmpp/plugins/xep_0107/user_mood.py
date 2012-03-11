"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp import Message
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import MatchXPath
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.plugins.xep_0107 import stanza, UserMood


log = logging.getLogger(__name__)


class xep_0107(base_plugin):

    """
    XEP-0107: User Mood
    """

    def plugin_init(self):
        self.xep = '0107'
        self.description = 'User Mood'
        self.stanza = stanza

    def post_init(self):
        base_plugin.post_init(self)

        pubsub_stanza = self.xmpp['xep_0060'].stanza
        register_stanza_plugin(Message, UserMood)
        register_stanza_plugin(pubsub_stanza.EventItem, UserMood)

        self.xmpp['xep_0030'].add_feature(UserMood.namespace)
        self.xmpp['xep_0163'].add_interest(UserMood.namespace)
        self.xmpp['xep_0060'].map_node_event(UserMood.namespace, 'user_mood')

    def publish_mood(self, value=None, text=None, options=None, 
                     ifrom=None, block=True, callback=None, timeout=None):
        """
        Publish the user's current mood.

        Arguments:
            value    -- The name of the mood to publish.
            text     -- Optional natural-language description or reason
                        for the mood.
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
        mood = UserMood()
        mood['value'] = value
        mood['text'] = text
        self.xmpp['xep_0163'].publish(mood,
                node=UserMood.namespace,
                options=options,
                ifrom=ifrom,
                block=block,
                callback=callback,
                timeout=timeout)

    def stop(self, ifrom=None, block=True, callback=None, timeout=None):
        """
        Clear existing user mood information to stop notifications.

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
        mood = UserMood()
        self.xmpp['xep_0163'].publish(mood, 
                node=UserMood.namespace,
                ifrom=ifrom,
                block=block,
                callback=callback,
                timeout=timeout)
