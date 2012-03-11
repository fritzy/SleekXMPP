"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import MatchXPath
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.plugins.xep_0108 import stanza, UserActivity


log = logging.getLogger(__name__)


class xep_0108(base_plugin):

    """
    XEP-0108: User Activity
    """

    def plugin_init(self):
        self.xep = '0108'
        self.description = 'User Activity'
        self.stanza = stanza

    def post_init(self):
        base_plugin.post_init(self)

        pubsub_stanza = self.xmpp['xep_0060'].stanza
        register_stanza_plugin(pubsub_stanza.EventItem, UserActivity)

        self.xmpp['xep_0030'].add_feature(UserActivity.namespace)
        self.xmpp['xep_0163'].add_interest(UserActivity.namespace)
        self.xmpp['xep_0060'].map_node_event(UserActivity.namespace, 'user_activity')

    def publish_activity(self, general, specific=None, text=None, options=None, 
                     ifrom=None, block=True, callback=None, timeout=None):
        """
        Publish the user's current activity.

        Arguments:
            general  -- The required general category of the activity.
            specific -- Optional specific activity being done as part
                        of the general category.
            text     -- Optional natural-language description or reason
                        for the activity.
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
        activity = UserActivity()
        activity['value'] = (general, specific)
        activity['text'] = text
        self.xmpp['xep_0163'].publish(activity,
                node=UserActivity.namespace,
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
        activity = UserActivity()
        self.xmpp['xep_0163'].publish(activity, 
                node=UserActivity.namespace,
                ifrom=ifrom,
                block=block,
                callback=callback,
                timeout=timeout)
