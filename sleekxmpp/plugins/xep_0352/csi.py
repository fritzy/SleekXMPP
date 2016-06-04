"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2016 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.stanza import StreamFeatures
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins.base import BasePlugin
from sleekxmpp.plugins.xep_0352 import stanza, Active, Inactive, ClientStateIndication


log = logging.getLogger(__name__)


class XEP_0352(BasePlugin):

    """
    XEP-0352: Client State Indication
    """

    name = 'xep_0352'
    description = 'XEP-0352: Client State Indication'
    dependencies = set()
    stanza = stanza
    default_config = {
        "order": 12000,
    }

    def plugin_init(self):
        """Start the XEP-0352 plugin."""

        self.enabled = False

        register_stanza_plugin(StreamFeatures, ClientStateIndication)
        self.xmpp.register_stanza(stanza.Active)
        self.xmpp.register_stanza(stanza.Inactive)

        self.xmpp.register_feature('csi',
                self._handle_csi_feature,
                restart=False,
                order=self.order)


    def plugin_end(self):
        if self.xmpp.is_component:
            return

        self.xmpp.unregister_feature('csi', self.order)
        self.xmpp.remove_stanza(stanza.Active)
        self.xmpp.remove_stanza(stanza.Inactive)

    def send_active(self):
        """Send an 'active' state"""
        if self.enabled:
            self.xmpp.send_raw(str(stanza.Active(self.xmpp)))

    def send_inactive(self):
        """Send an 'active' state"""
        if self.enabled:
            self.xmpp.send_raw(str(stanza.Inactive(self.xmpp)))

    def _handle_csi_feature(self, features):
        """
        Enable CSI
        """
        if 'csi' in self.xmpp.features:
            log.debug('CSI already enabled')
            return False
        self.enabled = True
        self.xmpp.event('csi_enabled', features)
        return False
