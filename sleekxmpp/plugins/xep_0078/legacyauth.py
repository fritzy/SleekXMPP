"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging
import hashlib
import random

from sleekxmpp.stanza import Iq, StreamFeatures
from sleekxmpp.xmlstream import ElementBase, ET, register_stanza_plugin
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.plugins.xep_0078 import stanza


log = logging.getLogger(__name__)


class xep_0078(base_plugin):

    """
    XEP-0078 NON-SASL Authentication

    This XEP is OBSOLETE in favor of using SASL, so DO NOT use this plugin
    unless you are forced to use an old XMPP server implementation.
    """

    def plugin_init(self):
        self.xep = "0078"
        self.description = "Non-SASL Authentication"
        self.stanza = stanza

        self.xmpp.register_feature('auth',
                self._handle_auth,
                restart=False,
                order=self.config.get('order', 15))

        register_stanza_plugin(Iq, stanza.IqAuth)
        register_stanza_plugin(StreamFeatures, stanza.AuthFeature)


    def _handle_auth(self, features):
        # If we can or have already authenticated with SASL, do nothing.
        if 'mechanisms' in features['features']:
            return False
        if self.xmpp.authenticated:
            return False

        log.debug("Starting jabber:iq:auth Authentication")

        # Step 1: Request the auth form
        iq = self.xmpp.Iq()
        iq['type'] = 'get'
        iq['to'] = self.xmpp.boundjid.host
        iq['auth']['username'] = self.xmpp.boundjid.user

        try:
            resp = iq.send(now=True)
        except IqError:
            log.info("Authentication failed: %s", resp['error']['condition'])
            self.xmpp.event('failed_auth', direct=True)
            self.xmpp.disconnect()
            return True
        except IqTimeout:
            log.info("Authentication failed: %s", 'timeout')
            self.xmpp.event('failed_auth', direct=True)
            self.xmpp.disconnect()
            return True

        # Step 2: Fill out auth form for either password or digest auth
        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['auth']['username'] = self.xmpp.boundjid.user

        # A resource is required, so create a random one if necessary
        if self.xmpp.boundjid.resource:
            iq['auth']['resource'] = self.xmpp.boundjid.resource
        else:
            iq['auth']['resource'] = '%s' % random.random()

        if 'digest' in resp['auth']['fields']:
            log.debug('Authenticating via jabber:iq:auth Digest')
            if sys.version_info < (3, 0):
                stream_id = bytes(self.xmpp.stream_id)
                password = bytes(self.xmpp.password)
            else:
                stream_id = bytes(self.xmpp.stream_id, encoding='utf-8')
                password = bytes(self.xmpp.password, encoding='utf-8')

            digest = hashlib.sha1(b'%s%s' % (stream_id, password)).hexdigest()
            iq['auth']['digest'] = digest
        else:
            log.warning('Authenticating via jabber:iq:auth Plain.')
            iq['auth']['password'] = self.xmpp.password

        # Step 3: Send credentials
        try:
            result = iq.send(now=True)
        except IqError as err:
            log.info("Authentication failed")
            self.xmpp.disconnect()
            self.xmpp.event("failed_auth", direct=True)
        except IqTimeout:
            log.info("Authentication failed")
            self.xmpp.disconnect()
            self.xmpp.event("failed_auth", direct=True)

        self.xmpp.features.add('auth')

        self.xmpp.authenticated = True
        log.debug("Established Session")
        self.xmpp.sessionstarted = True
        self.xmpp.session_started_event.set()
        self.xmpp.event('session_start')

        return True
