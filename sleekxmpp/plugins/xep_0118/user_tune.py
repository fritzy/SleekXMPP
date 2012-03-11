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
from sleekxmpp.plugins.xep_0118 import stanza, UserTune


log = logging.getLogger(__name__)


class xep_0118(base_plugin):

    """
    XEP-0118: User Tune
    """

    def plugin_init(self):
        self.xep = '0118'
        self.description = 'User Tune'
        self.stanza = stanza

    def post_init(self):
        base_plugin.post_init(self)
        pubsub_stanza = self.xmpp['xep_0060'].stanza
        register_stanza_plugin(pubsub_stanza.EventItem, UserTune)
        self.xmpp['xep_0030'].add_feature(UserTune.namespace)
        self.xmpp['xep_0163'].add_interest(UserTune.namespace)
        self.xmpp['xep_0060'].map_node_event(UserTune.namespace, 'user_tune')

    def publish_tune(self, artist=None, length=None, rating=None, source=None,
                     title=None, track=None, uri=None, options=None, 
                     ifrom=None, block=True, callback=None, timeout=None):
        """
        Publish the user's current tune.

        Arguments:
            artist   -- The artist or performer of the song.
            length   -- The length of the song in seconds.
            rating   -- The user's rating of the song (from 1 to 10)
            source   -- The album name, website, or other source of the song.
            title    -- The title of the song.
            track    -- The song's track number, or other unique identifier.
            uri      -- A URL to more information about the song.
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
        tune = UserTune()
        tune['artist'] = artist
        tune['length'] = length
        tune['rating'] = rating
        tune['source'] = source
        tune['title'] = title
        tune['track'] = track
        tune['uri'] = uri
        return self.xmpp['xep_0163'].publish(tune, 
                node=UserTune.namespace,
                options=options,
                ifrom=ifrom,
                block=block,
                callback=callback,
                timeout=timeout)

    def stop(self, ifrom=None, block=True, callback=None, timeout=None):
        """
        Clear existing user tune information to stop notifications.

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
        tune = UserTune()
        return self.xmpp['xep_0163'].publish(tune, 
                node=UserTune.namespace,
                ifrom=ifrom,
                block=block,
                callback=callback,
                timeout=timeout)
