"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permissio
"""

import logging

from sleekxmpp.stanza import Message, Error, StreamFeatures
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.xmlstream.matcher import StanzaPath, MatchMany
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.plugins.xep_0079 import stanza


log = logging.getLogger(__name__)


class XEP_0079(BasePlugin):

    """
    XEP-0079 Advanced Message Processing
    """

    name = 'xep_0079'
    description = 'XEP-0079: Advanced Message Processing'
    dependencies = set(['xep_0030'])
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Message, stanza.AMP)
        register_stanza_plugin(Error, stanza.InvalidRules)
        register_stanza_plugin(Error, stanza.UnsupportedConditions)
        register_stanza_plugin(Error, stanza.UnsupportedActions)
        register_stanza_plugin(Error, stanza.FailedRules)

        self.xmpp.register_handler(
                Callback('AMP Response',
                    MatchMany([
                        StanzaPath('message/error/failed_rules'),
                        StanzaPath('message/amp')
                    ]),
                    self._handle_amp_response))

        if not self.xmpp.is_component:
            self.xmpp.register_feature('amp',
                    self._handle_amp_feature,
                    restart=False,
                    order=9000)
            register_stanza_plugin(StreamFeatures, stanza.AMPFeature)

    def plugin_end(self):
        self.xmpp.remove_handler('AMP Response')

    def _handle_amp_response(self, msg):
        log.debug('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        if msg['type'] == 'error':
            self.xmpp.event('amp_error', msg)
        elif msg['amp']['status'] in ('alert', 'notify'):
            self.xmpp.event('amp_%s' % msg['amp']['status'], msg)

    def _handle_amp_feature(self, features):
        log.debug('Advanced Message Processing is available.')
        self.xmpp.features.add('amp')

    def discover_support(self, jid=None, **iqargs):
        if jid is None:
            if self.xmpp.is_component:
                jid = self.xmpp.server_host
            else:
                jid = self.xmpp.boundjid.host

        return self.xmpp['xep_0030'].get_info(
                jid=jid,
                node='http://jabber.org/protocol/amp',
                **iqargs)
