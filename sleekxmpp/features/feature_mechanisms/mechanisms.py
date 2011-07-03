"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.xmlstream import RestartStream
from sleekxmpp.xmlstream.matcher import *
from sleekxmpp.xmlstream.handler import *
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.features.feature_mechanisms import stanza


log = logging.getLogger(__name__)


class feature_mechanisms(base_plugin):

    def plugin_init(self):
        self.name = 'SASL Mechanisms'
        self.rfc = '6120'
        self.description = "SASL Stream Feature"
        self.stanza = stanza

        self.xmpp.register_stanza(stanza.Success)
        self.xmpp.register_stanza(stanza.Failure)
        self.xmpp.register_stanza(stanza.Auth)

        self._mechanism_handlers = {}
        self._mechanism_priorities = []

        self.xmpp.register_handler(
                Callback('SASL Success',
                         MatchXPath(stanza.Success.tag_name()),
                         self._handle_success,
                         instream=True,
                         once=True))
        self.xmpp.register_handler(
                Callback('SASL Failure',
                         MatchXPath(stanza.Failure.tag_name()),
                         self._handle_fail,
                         instream=True,
                         once=True))

        self.xmpp.register_feature('mechanisms',
                self._handle_sasl_auth,
                restart=True,
                order=self.config.get('order', 100))

    def register(self, name, handler, priority=0):
        """
        Register a handler for a SASL authentication mechanism.

        Arguments:
            name     -- The name of the mechanism (all caps)
            handler  -- The function that will perform the
                        authentication. The function must
                        return True if it is able to carry
                        out the authentication, False if
                        a required condition is not met.
            priority -- An integer value indicating the
                        preferred ordering for the mechanism.
                        High values will be attempted first.
        """
        self._mechanism_handlers[name] = handler
        self._mechanism_priorities.append((priority, name))
        self._mechanism_priorities.sort(reverse=True)

    def remove(self, name):
        """
        Remove support for a given SASL authentication mechanism.

        Arguments:
            name -- The name of the mechanism to remove (all caps)
        """
        if name in self._mechanism_handlers:
            del self._mechanism_handlers[name]

        p = self._mechanism_priorities
        self._mechanism_priorities = [i for i in p if i[1] != name]

    def _handle_sasl_auth(self, features):
        """
        Handle authenticating using SASL.

        Arguments:
            features -- The stream features stanza.
        """
        if 'mechanisms' in self.xmpp.features:
            # SASL authentication has already succeeded, but the
            # server has incorrectly offered it again.
            return False

        for priority, mech in self._mechanism_priorities:
            if mech in features['mechanisms']:
                log.debug('Attempt to use SASL %s' % mech)
                if self._mechanism_handlers[mech]():
                    break
        else:
            log.error("No appropriate login method.")
            self.xmpp.event("no_auth", direct=True)
            self.xmpp.disconnect()

        return True

    def _handle_success(self, stanza):
        """SASL authentication succeeded. Restart the stream."""
        self.xmpp.authenticated = True
        self.xmpp.features.add('mechanisms')
        raise RestartStream()

    def _handle_fail(self, stanza):
        """SASL authentication failed. Disconnect and shutdown."""
        log.info("Authentication failed.")
        self.xmpp.event("failed_auth", direct=True)
        self.xmpp.disconnect()
        log.debug("Starting SASL Auth")
        return True
