"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.thirdparty import suelta

from sleekxmpp.stanza import StreamFeatures
from sleekxmpp.xmlstream import RestartStream, register_stanza_plugin
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

        self.use_mech = self.config.get('use_mech', None)

        def tls_active():
            return 'starttls' in self.xmpp.features

        def basic_callback(mech, values):
            if 'username' in values:
                values['username'] = self.xmpp.boundjid.user
            if 'password' in values:
                values['password'] = self.xmpp.password
            mech.fulfill(values)

        sasl_callback = self.config.get('sasl_callback', None)
        if sasl_callback is None:
            sasl_callback = basic_callback

        self.mech = None
        self.sasl = suelta.SASL(self.xmpp.boundjid.domain, 'xmpp',
                                username=self.xmpp.boundjid.user,
                                sec_query=suelta.sec_query_allow,
                                request_values=sasl_callback,
                                tls_active=tls_active,
                                mech=self.use_mech)

        register_stanza_plugin(StreamFeatures, stanza.Mechanisms)

        self.xmpp.register_stanza(stanza.Success)
        self.xmpp.register_stanza(stanza.Failure)
        self.xmpp.register_stanza(stanza.Auth)
        self.xmpp.register_stanza(stanza.Challenge)
        self.xmpp.register_stanza(stanza.Response)

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
        self.xmpp.register_handler(
                Callback('SASL Challenge',
                         MatchXPath(stanza.Challenge.tag_name()),
                         self._handle_challenge))

        self.xmpp.register_feature('mechanisms',
                self._handle_sasl_auth,
                restart=True,
                order=self.config.get('order', 100))

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

        mech_list = features['mechanisms']
        self.mech = self.sasl.choose_mechanism(mech_list)

        if self.mech is not None:
            resp = stanza.Auth(self.xmpp)
            resp['mechanism'] = self.mech.name
            resp['value'] = self.mech.process()
            resp.send(now=True)
        else:
            log.error("No appropriate login method.")
            self.xmpp.event("no_auth", direct=True)
            self.xmpp.disconnect()
        return True

    def _handle_challenge(self, stanza):
        """SASL challenge received. Process and send response."""
        resp = self.stanza.Response(self.xmpp)
        resp['value'] = self.mech.process(stanza['value'])
        resp.send(now=True)

    def _handle_success(self, stanza):
        """SASL authentication succeeded. Restart the stream."""
        self.xmpp.authenticated = True
        self.xmpp.features.add('mechanisms')
        raise RestartStream()

    def _handle_fail(self, stanza):
        """SASL authentication failed. Disconnect and shutdown."""
        log.info("Authentication failed: %s", stanza['condition'])
        self.xmpp.event("failed_auth", stanza, direct=True)
        self.xmpp.disconnect()
        return True
