"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.plugins.google.auth import stanza


log = logging.getLogger(__name__)


class GoogleAuth(BasePlugin):

    """
    Google: Auth Extensions (JID Domain Discovery, OAuth2)

    Also see:
        <https://developers.google.com/talk/jep_extensions/jid_domain_change>
        <https://developers.google.com/talk/jep_extensions/oauth>
    """

    name = 'google_auth'
    description = 'Google: Auth Extensions (JID Domain Discovery, OAuth2)'
    dependencies = set(['feature_mechanisms'])
    stanza = stanza

    def plugin_init(self):
        self.xmpp.namespace_map['http://www.google.com/talk/protocol/auth'] = 'ga'

        register_stanza_plugin(self.xmpp['feature_mechanisms'].stanza.Auth,
                               stanza.GoogleAuth)

        self.xmpp.add_filter('out', self._auth)

    def plugin_end(self):
        self.xmpp.del_filter('out', self._auth)

    def _auth(self, stanza):
        if isinstance(stanza, self.xmpp['feature_mechanisms'].stanza.Auth):
            stanza.stream = self.xmpp
            stanza['google']['client_uses_full_bind_result'] = True
            if stanza['mechanism'] == 'X-OAUTH2':
                stanza['google']['service'] = 'oauth2'
            print(stanza)
        return stanza
