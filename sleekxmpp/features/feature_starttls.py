"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.stanza.stream import tls
from sleekxmpp.xmlstream import RestartStream
from sleekxmpp.xmlstream.matcher import *
from sleekxmpp.xmlstream.handler import *
from sleekxmpp.plugins.base import base_plugin


log = logging.getLogger(__name__)


class feature_starttls(base_plugin):

    def plugin_init(self):
        self.name = "STARTTLS"
        self.rfc = '6120'
        self.description = "STARTTLS Stream Feature"

        self.xmpp.register_stanza(tls.Proceed)
        self.xmpp.register_handler(
                Callback('STARTTLS Proceed',
                        MatchXPath(tls.Proceed.tag_name()),
                        self._handle_starttls_proceed,
                        instream=True))
        self.xmpp.register_feature('starttls',
                self._handle_starttls,
                restart=True,
                order=self.config.get('order', 0))

    def _handle_starttls(self, features):
        """
        Handle notification that the server supports TLS.

        Arguments:
            features -- The stream:features element.
        """
        if not self.xmpp.use_tls:
            return False
        elif self.xmpp.ssl_support:
            self.xmpp.send(features['starttls'], now=True)
            return True
        else:
            log.warning("The module tlslite is required to log in" +\
                            " to some servers, and has not been found.")
            return False

    def _handle_starttls_proceed(self, proceed):
        """Restart the XML stream when TLS is accepted."""
        log.debug("Starting TLS")
        if self.xmpp.start_tls():
            self.xmpp.features.append('starttls')
            raise RestartStream()
