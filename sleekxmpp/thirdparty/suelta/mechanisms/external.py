from sleekxmpp.thirdparty.suelta.util import bytes
from sleekxmpp.thirdparty.suelta.sasl import Mechanism, register_mechanism
from sleekxmpp.thirdparty.suelta.exceptions import SASLError, SASLCancelled



class EXTERNAL(Mechanism):

    def __init__(self, sasl, name):
        super(EXTERNAL, self).__init__(sasl, name)
        self.check_values(['jid', 'certificate_jids'])

    def process(self, challenge=None):
        return b''

    def okay(self):
        return True


register_mechanism('EXTERNAL', 100, EXTERNAL, use_hashes=False)
