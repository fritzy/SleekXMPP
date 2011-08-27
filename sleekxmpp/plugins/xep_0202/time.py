"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.stanza.iq import Iq
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.plugins import xep_0082
from sleekxmpp.plugins.xep_0202 import stanza


log = logging.getLogger(__name__)


class xep_0202(base_plugin):

    """
    XEP-0202: Entity Time
    """

    def plugin_init(self):
        """Start the XEP-0203 plugin."""
        self.xep = '0202'
        self.description = 'Entity Time'
        self.stanza = stanza

        self.tz_offset = self.config.get('tz_offset', 0)

        # As a default, respond to time requests with the
        # local time returned by XEP-0082. However, a
        # custom function can be supplied which accepts
        # the JID of the entity to query for the time.
        self.local_time = self.config.get('local_time', None)
        if not self.local_time:
            self.local_time = lambda x: xep_0082.datetime(offset=self.tz_offset)

        self.xmpp.registerHandler(
            Callback('Entity Time',
                 StanzaPath('iq/entity_time'),
                 self._handle_time_request))
        register_stanza_plugin(Iq, stanza.EntityTime)

    def post_init(self):
        """Handle cross-plugin interactions."""
        base_plugin.post_init(self)
        self.xmpp['xep_0030'].add_feature('urn:xmpp:time')


    def _handle_time_request(self, iq):
        """
        Respond to a request for the local time.

        The time is taken from self.local_time(), which may be replaced
        during plugin configuration with a function that maps JIDs to
        times.

        Arguments:
            iq -- The Iq time request stanza.
        """
        iq.reply()
        iq['entity_time']['time'] = self.local_time(iq['to'])
        iq.send()

    def get_entity_time(self, to, ifrom=None, **iqargs):
        """
        Request the time from another entity.

        Arguments:
            to       -- JID of the entity to query.
            ifrom    -- Specifiy the sender's JID.
            block    -- If true, block and wait for the stanzas' reply.
            timeout  -- The time in seconds to block while waiting for
                        a reply. If None, then wait indefinitely.
            callback -- Optional callback to execute when a reply is
                        received instead of blocking and waiting for
                        the reply.
        """
        iq = self.xmpp.Iq()
        iq['type'] = 'get'
        iq['to'] = to
        iq['from'] = ifrom
        iq.enable('entity_time')
        return iq.send(**iqargs)
