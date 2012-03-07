"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.stanza import Iq, StreamFeatures
from sleekxmpp.features.feature_rosterver import stanza
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins.base import base_plugin


log = logging.getLogger(__name__)


class feature_rosterver(base_plugin):

    def plugin_init(self):
        self.name = 'Roster Versioning'
        self.rfc = '6121'
        self.description = 'Roster Versioning'
        self.stanza = stanza

        self.xmpp.register_feature('rosterver',
                self._handle_rosterver,
                restart=False,
                order=9000)

        register_stanza_plugin(StreamFeatures, stanza.RosterVer)

    def _handle_rosterver(self, features):
        """Enable using roster versioning.

        Arguments:
            features -- The stream features stanza.
        """
        log.debug("Enabling roster versioning.")
        self.xmpp.features.add('rosterver')
