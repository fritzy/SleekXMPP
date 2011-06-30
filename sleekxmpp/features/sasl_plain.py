import base64
import sys
import logging

from sleekxmpp.stanza.stream import sasl
from sleekxmpp.plugins.base import base_plugin


log = logging.getLogger(__name__)


class sasl_plain(base_plugin):

    def plugin_init(self):
        self.name = 'SASL PLAIN'
        self.rfc = '6120'
        self.description = 'SASL PLAIN Mechanism'

        self.xmpp.register_sasl_mechanism('PLAIN',
                self._handle_plain,
                priority=self.config.get('priority', 1))

    def _handle_plain(self):
        if not self.xmpp.boundjid.user:
            return False

        if sys.version_info < (3, 0):
            user = bytes(self.xmpp.boundjid.user)
            password = bytes(self.xmpp.password)
        else:
            user = bytes(self.xmpp.boundjid.user, 'utf-8')
            password = bytes(self.xmpp.password, 'utf-8')

        auth = base64.b64encode(b'\x00' + user + \
                                b'\x00' + password).decode('utf-8')

        resp = sasl.Auth(self.xmpp)
        resp['mechanism'] = 'PLAIN'
        resp['value'] = auth
        resp.send(now=True)
        return True
