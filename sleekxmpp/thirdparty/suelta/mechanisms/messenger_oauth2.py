from sleekxmpp.thirdparty.suelta.util import bytes
from sleekxmpp.thirdparty.suelta.sasl import Mechanism, register_mechanism


class X_MESSENGER_OAUTH2(Mechanism):

    def __init__(self, sasl, name):
        super(X_MESSENGER_OAUTH2, self).__init__(sasl, name)
        self.check_values(['access_token'])

    def process(self, challenge=None):
        return bytes(self.values['access_token'])

    def okay(self):
        return True

register_mechanism('X-MESSENGER-OAUTH2', 10, X_MESSENGER_OAUTH2, use_hashes=False)
