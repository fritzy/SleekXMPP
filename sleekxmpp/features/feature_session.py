"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.xmlstream.matcher import *
from sleekxmpp.xmlstream.handler import *
from sleekxmpp.plugins.base import base_plugin


log = logging.getLogger(__name__)


class feature_session(base_plugin):

    def plugin_init(self):
        self.name = 'Start Session'
        self.rfc = '3920'
        self.description = 'Start Session Stream Feature'

        self.xmpp.register_feature('session',
                self._handle_start_session,
                restart=False,
                order=10001)

    def _handle_start_session(self, features):
        """
        Handle the start of the session.

        Arguments:
            feature -- The stream features element.
        """
        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq.enable('session')
        response = iq.send(now=True)

        log.debug("Established Session")
        self.xmpp.sessionstarted = True
        self.xmpp.session_started_event.set()
        self.xmpp.event("session_start")
