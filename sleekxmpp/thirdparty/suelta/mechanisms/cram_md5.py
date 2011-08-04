import sys
import hmac

from sleekxmpp.thirdparty.suelta.util import hash, bytes
from sleekxmpp.thirdparty.suelta.sasl import Mechanism, register_mechanism
from sleekxmpp.thirdparty.suelta.exceptions import SASLError, SASLCancelled


class CRAM_MD5(Mechanism):

    """
    """

    def __init__(self, sasl, name):
        """
        """
        super(CRAM_MD5, self).__init__(sasl, name, 2)

        self.hash = hash(name[5:])
        if self.hash is None:
            raise SASLCancelled(self.sasl, self)
        if not self.sasl.tls_active():
            if not self.sasl.sec_query(self, 'CRAM-MD5'):
                raise SASLCancelled(self.sasl, self)

    def prep(self):
        """
        """
        if 'savepass' not in self.values:
            if self.sasl.sec_query(self, 'CLEAR-PASSWORD'):
                self.values['savepass'] = True

        if 'savepass' not in self.values:
            del self.values['password']

    def process(self, challenge):
        """
        """
        if challenge is None:
            return None

        self.check_values(['username', 'password'])
        username = bytes(self.values['username'])
        password = bytes(self.values['password'])

        mac = hmac.HMAC(key=password, digestmod=self.hash)

        mac.update(challenge)

        return username + b' ' + bytes(mac.hexdigest())

    def okay(self):
        """
        """
        return True

    def get_user(self):
        """
        """
        return self.values['username']


register_mechanism('CRAM-', 20, CRAM_MD5)
