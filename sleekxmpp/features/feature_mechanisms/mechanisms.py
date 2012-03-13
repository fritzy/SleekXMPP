"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.thirdparty import suelta
from sleekxmpp.thirdparty.suelta.exceptions import SASLCancelled, SASLError

from sleekxmpp.stanza import StreamFeatures
from sleekxmpp.xmlstream import RestartStream, register_stanza_plugin
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.xmlstream.matcher import MatchXPath
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.features.feature_mechanisms import stanza


log = logging.getLogger(__name__)


class FeatureMechanisms(BasePlugin):

    name = 'feature_mechanisms'
    description = 'RFC 6120: Stream Feature: SASL'
    dependencies = set()
    stanza = stanza

    def plugin_init(self):
        self.use_mech = self.config.get('use_mech', None)

        if not self.use_mech and not self.xmpp.boundjid.user:
            self.use_mech = 'ANONYMOUS'

        def tls_active():
            return 'starttls' in self.xmpp.features

        def basic_callback(mech, values):
            creds = self.xmpp.credentials
            for value in values:
                if value == 'username':
                    values['username'] = self.xmpp.boundjid.user
                elif value == 'password':
                    values['password'] = creds['password']
                elif value == 'email':
                    jid = self.xmpp.boundjid.bare
                    values['email'] = creds.get('email', jid)
                elif value in creds:
                    values[value] = creds[value]
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

        self.mech_list = set()
        self.attempted_mechs = set()

        register_stanza_plugin(StreamFeatures, stanza.Mechanisms)

        self.xmpp.register_stanza(stanza.Success)
        self.xmpp.register_stanza(stanza.Failure)
        self.xmpp.register_stanza(stanza.Auth)
        self.xmpp.register_stanza(stanza.Challenge)
        self.xmpp.register_stanza(stanza.Response)
        self.xmpp.register_stanza(stanza.Abort)

        self.xmpp.register_handler(
                Callback('SASL Success',
                         MatchXPath(stanza.Success.tag_name()),
                         self._handle_success,
                         instream=True))
        self.xmpp.register_handler(
                Callback('SASL Failure',
                         MatchXPath(stanza.Failure.tag_name()),
                         self._handle_fail,
                         instream=True))
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

        if not self.use_mech:
            self.mech_list = set(features['mechanisms'])
        else:
            self.mech_list = set([self.use_mech])
        return self._send_auth()

    def _send_auth(self):
        mech_list = self.mech_list - self.attempted_mechs
        self.mech = self.sasl.choose_mechanism(mech_list)

        if mech_list and self.mech is not None:
            resp = stanza.Auth(self.xmpp)
            resp['mechanism'] = self.mech.name
            try:
                resp['value'] = self.mech.process()
            except SASLCancelled:
                self.attempted_mechs.add(self.mech.name)
                self._send_auth()
            except SASLError:
                self.attempted_mechs.add(self.mech.name)
                self._send_auth()
            else:
                resp.send(now=True)
        else:
            log.error("No appropriate login method.")
            self.xmpp.event("no_auth", direct=True)
            self.xmpp.disconnect()
        return True

    def _handle_challenge(self, stanza):
        """SASL challenge received. Process and send response."""
        resp = self.stanza.Response(self.xmpp)
        try:
            resp['value'] = self.mech.process(stanza['value'])
        except SASLCancelled:
            self.stanza.Abort(self.xmpp).send()
        except SASLError:
            self.stanza.Abort(self.xmpp).send()
        else:
            resp.send(now=True)

    def _handle_success(self, stanza):
        """SASL authentication succeeded. Restart the stream."""
        self.attempted_mechs = set()
        self.xmpp.authenticated = True
        self.xmpp.features.add('mechanisms')
        raise RestartStream()

    def _handle_fail(self, stanza):
        """SASL authentication failed. Disconnect and shutdown."""
        self.attempted_mechs.add(self.mech.name)
        log.info("Authentication failed: %s", stanza['condition'])
        self.xmpp.event("failed_auth", stanza, direct=True)
        self._send_auth()
        return True
