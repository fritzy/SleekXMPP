"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.stanza import StreamFeatures
from sleekxmpp.xmlstream import RestartStream, register_stanza_plugin
from sleekxmpp.xmlstream.matcher import *
from sleekxmpp.xmlstream.handler import *
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.features.feature_starttls import stanza


log = logging.getLogger(__name__)


class feature_starttls(base_plugin):

    def plugin_init(self):
        self.name = "STARTTLS"
        self.rfc = '6120'
        self.description = "STARTTLS Stream Feature"
        self.stanza = stanza

        self.xmpp.register_handler(
                Callback('STARTTLS Proceed',
                        MatchXPath(stanza.Proceed.tag_name()),
                        self._handle_starttls_proceed,
                        instream=True))
        self.xmpp.register_feature('starttls',
                self._handle_starttls,
                restart=True,
                order=self.config.get('order', 0))

        self.xmpp.register_stanza(stanza.Proceed)
        self.xmpp.register_stanza(stanza.Failure)
        register_stanza_plugin(StreamFeatures, stanza.STARTTLS)

    def _handle_starttls(self, features):
        """
        Handle notification that the server supports TLS.

        Arguments:
            features -- The stream:features element.
        """
        if 'starttls' in self.xmpp.features:
            # We have already negotiated TLS, but the server is
            # offering it again, against spec.
            return False
        elif not self.xmpp.use_tls:
            return False
        elif self.xmpp.ssl_support:
            self.xmpp.send(features['starttls'], now=True)
            return True
        else:
            log.warning("The module tlslite is required to log in" + \
                        " to some servers, and has not been found.")
            return False

    def _handle_starttls_proceed(self, proceed):
        """Restart the XML stream when TLS is accepted."""
        log.debug("Starting TLS")
        if self.xmpp.start_tls():
            self.xmpp.features.add('starttls')
            raise RestartStream()
