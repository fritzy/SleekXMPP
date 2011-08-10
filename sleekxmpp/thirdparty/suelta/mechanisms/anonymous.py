from sleekxmpp.thirdparty.suelta.sasl import Mechanism, register_mechanism
from sleekxmpp.thirdparty.suelta.exceptions import SASLError, SASLCancelled


class ANONYMOUS(Mechanism):

    """
    """

    def __init__(self, sasl, name):
        """
        """
        super(ANONYMOUS, self).__init__(sasl, name, 0)

    def get_values(self):
        """
        """
        return {}

    def process(self, challenge=None):
        """
        """
        return b'Anonymous, Suelta'

    def okay(self):
        """
        """
        return True

    def get_user(self):
        """
        """
        return 'anonymous'


register_mechanism('ANONYMOUS', 0, ANONYMOUS, use_hashes=False)
