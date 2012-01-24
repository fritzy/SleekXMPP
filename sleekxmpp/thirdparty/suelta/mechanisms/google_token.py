from sleekxmpp.thirdparty.suelta.util import bytes
from sleekxmpp.thirdparty.suelta.sasl import Mechanism, register_mechanism
from sleekxmpp.thirdparty.suelta.exceptions import SASLError, SASLCancelled



class X_GOOGLE_TOKEN(Mechanism):

    def __init__(self, sasl, name):
        super(X_GOOGLE_TOKEN, self).__init__(sasl, name)
        self.check_values(['email', 'access_token'])

    def process(self, challenge=None):
        email = bytes(self.values['email'])
        token = bytes(self.values['access_token'])
        return b'\x00' + email + b'\x00' + token

    def okay(self):
        return True


register_mechanism('X-GOOGLE-TOKEN', 3, X_GOOGLE_TOKEN, use_hashes=False)
