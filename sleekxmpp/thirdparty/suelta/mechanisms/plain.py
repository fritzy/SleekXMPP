import sys

from sleekxmpp.thirdparty.suelta.util import bytes
from sleekxmpp.thirdparty.suelta.sasl import Mechanism, register_mechanism
from sleekxmpp.thirdparty.suelta.exceptions import SASLError, SASLCancelled


class PLAIN(Mechanism):

    """
    """

    def __init__(self, sasl, name):
        """
        """
        super(PLAIN, self).__init__(sasl, name)

        if not self.sasl.tls_active():
            if not self.sasl.sec_query(self, '-ENCRYPTION, PLAIN'):
                raise SASLCancelled(self.sasl, self)
        else:
            if not self.sasl.sec_query(self, '+ENCRYPTION, PLAIN'):
                raise SASLCancelled(self.sasl, self)

        self.check_values(['username', 'password'])

    def prep(self):
        """
        Prepare for processing by deleting the password if
        the user has not approved storing it in the clear.
        """
        if 'savepass' not in self.values:
            if self.sasl.sec_query(self, 'CLEAR-PASSWORD'):
                self.values['savepass'] = True

        if 'savepass' not in self.values:
            del self.values['password']

        return True

    def process(self, challenge=None):
        """
        Process a challenge request and return the response.

        :param challenge: A challenge issued by the server that
                          must be answered for authentication.
        """
        user = bytes(self.values['username'])
        password = bytes(self.values['password'])
        return b'\x00' + user + b'\x00' + password

    def okay(self):
        """
        Mutual authentication is not supported by PLAIN.

        :returns: ``True``
        """
        return True


register_mechanism('PLAIN', 1, PLAIN, use_hashes=False)
