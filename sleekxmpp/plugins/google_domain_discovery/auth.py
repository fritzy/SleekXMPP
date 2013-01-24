"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.stanza import Iq, Message
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.plugins.google_domain_discovery import stanza


log = logging.getLogger(__name__)


class GoogleDomainDiscovery(BasePlugin):

    """
    Google: JID Domain Discovery

    Also see <https://developers.google.com/talk/jep_extensions/jid_domain_change
    """

    name = 'google_domain_discovery'
    description = 'Google: JID Domain Discovery'
    dependencies = set(['feature_mechanisms'])
    stanza = stanza

    def plugin_init(self):
        self.xmpp.namespace_map[stanza.GoogleAuth.namespace] = 'ga'

        register_stanza_plugin(self.xmpp['feature_mechanisms'].stanza.Auth,
                               stanza.GoogleAuth)

        self.xmpp.add_filter('out', self._auth)

    def plugin_end(self):
        self.xmpp.del_filter('out', self._auth)

    def _auth(self, stanza):
        if isinstance(stanza, self.xmpp['feature_mechanisms'].stanza.Auth):
            stanza['use_full_bind_result'] = True
        return stanza
