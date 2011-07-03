import base64
import sys
import logging

from sleekxmpp.plugins.base import base_plugin


log = logging.getLogger(__name__)


class sasl_anonymous(base_plugin):

    def plugin_init(self):
        self.name = 'SASL ANONYMOUS'
        self.rfc = '6120'
        self.description = 'SASL ANONYMOUS Mechanism'

        self.xmpp.register_sasl_mechanism('ANONYMOUS',
                self._handle_anonymous,
                priority=self.config.get('priority', 0))

    def _handle_anonymous(self):
        if self.xmpp.boundjid.user:
            return False

        resp = self.xmpp['feature_sasl'].stanza.Auth(self.xmpp)
        resp['mechanism'] = 'ANONYMOUS'
        resp.send(now=True)

        return True
