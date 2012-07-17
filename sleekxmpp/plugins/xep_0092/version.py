"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

import sleekxmpp
from sleekxmpp import Iq
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.plugins.xep_0092 import Version, stanza


log = logging.getLogger(__name__)


class XEP_0092(BasePlugin):

    """
    XEP-0092: Software Version
    """

    name = 'xep_0092'
    description = 'XEP-0092: Software Version'
    dependencies = set(['xep_0030'])
    stanza = stanza

    def plugin_init(self):
        """
        Start the XEP-0092 plugin.
        """
        self.name = self.config.get('name', 'SleekXMPP')
        self.version = self.config.get('version', sleekxmpp.__version__)
        self.os = self.config.get('os', '')

        self.getVersion = self.get_version

        self.xmpp.register_handler(
                Callback('Software Version',
                         StanzaPath('iq@type=get/software_version'),
                         self._handle_version))

        register_stanza_plugin(Iq, Version)

    def plugin_end(self):
        self.xmpp.remove_handler('Software Version')
        self.xmpp['xep_0030'].del_feature(feature='jabber:iq:version')

    def session_bind(self, jid):
        self.xmpp.plugin['xep_0030'].add_feature('jabber:iq:version')

    def _handle_version(self, iq):
        """
        Respond to a software version query.

        Arguments:
            iq -- The Iq stanza containing the software version query.
        """
        iq.reply()
        iq['software_version']['name'] = self.name
        iq['software_version']['version'] = self.version
        iq['software_version']['os'] = self.os
        iq.send()

    def get_version(self, jid, ifrom=None):
        """
        Retrieve the software version of a remote agent.

        Arguments:
            jid -- The JID of the entity to query.
        """
        iq = self.xmpp.Iq()
        iq['to'] = jid
        iq['from'] = ifrom
        iq['type'] = 'get'
        iq['query'] = Version.namespace

        result = iq.send()

        if result and result['type'] != 'error':
            values = result['software_version'].values
            del values['lang']
            return values
        return False
