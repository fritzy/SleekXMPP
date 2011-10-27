import sys
import hmac
import random
from base64 import b64encode, b64decode

from sleekxmpp.thirdparty.suelta.util import hash, bytes, num_to_bytes, bytes_to_num, XOR
from sleekxmpp.thirdparty.suelta.sasl import Mechanism, register_mechanism
from sleekxmpp.thirdparty.suelta.exceptions import SASLError, SASLCancelled


def parse_challenge(challenge):
    """
    """
    items = {}
    for key, value in [item.split(b'=', 1) for item in challenge.split(b',')]:
        items[key] = value
    return items


class SCRAM_HMAC(Mechanism):

    """
    """

    def __init__(self, sasl, name):
        """
        """
        super(SCRAM_HMAC, self).__init__(sasl, name, 0)

        self._cb = False
        if name[-5:] == '-PLUS':
            name = name[:-5]
            self._cb = True

        self.hash = hash(name[6:])
        if self.hash is None:
            raise SASLCancelled(self.sasl, self)
        if not self.sasl.tls_active():
            if not self.sasl.sec_query(self, '-ENCRYPTION, SCRAM'):
                raise SASLCancelled(self.sasl, self)

        self._step = 0
        self._rspauth = False

    def HMAC(self, key, msg):
        """
        """
        return hmac.HMAC(key=key, msg=msg, digestmod=self.hash).digest()

    def Hi(self, text, salt, iterations):
        """
        """
        text = bytes(text)
        ui_1 = self.HMAC(text, salt + b'\0\0\0\01')
        ui = ui_1
        for i in range(iterations - 1):
            ui_1 = self.HMAC(text, ui_1)
            ui = XOR(ui, ui_1)
        return ui

    def H(self, text):
        """
        """
        return self.hash(text).digest()

    def prep(self):
        if 'password' in self.values:
            del self.values['password']

    def process(self, challenge=None):
        """
        """
        steps = {
            0: self.process_one,
            1: self.process_two,
            2: self.process_three
        }
        return steps[self._step](challenge)

    def process_one(self, challenge):
        """
        """
        vitals = ['username']
        if 'SaltedPassword' not in self.values:
            vitals.append('password')
        if 'Iterations' not in self.values:
            vitals.append('password')

        self.check_values(vitals)

        username = bytes(self.values['username'])

        self._step = 1
        self._cnonce = bytes(('%s' % random.random())[2:])
        self._soup = b'n=' + username + b',r=' + self._cnonce
        self._gs2header = b''

        if not self.sasl.tls_active():
            if self._cb:
                self._gs2header = b'p=tls-unique,,'
            else:
                self._gs2header = b'y,,'
        else:
            self._gs2header = b'n,,'

        return self._gs2header + self._soup

    def process_two(self, challenge):
        """
        """
        data = parse_challenge(challenge)

        self._step = 2
        self._soup += b',' + challenge + b','
        self._nonce = data[b'r']
        self._salt = b64decode(data[b's'])
        self._iter = int(data[b'i'])

        if self._nonce[:len(self._cnonce)] != self._cnonce:
            raise SASLCancelled(self.sasl, self)

        cbdata = self.sasl.tls_active()
        c = self._gs2header
        if not cbdata and self._cb:
            c += None

        r = b'c=' + b64encode(c).replace(b'\n', b'')
        r += b',r=' + self._nonce
        self._soup += r

        if 'Iterations' in self.values:
            if self.values['Iterations'] != self._iter:
                if 'SaltedPassword' in self.values:
                    del self.values['SaltedPassword']
        if 'Salt' in self.values:
            if self.values['Salt'] != self._salt:
                if 'SaltedPassword' in self.values:
                    del self.values['SaltedPassword']

        self.values['Iterations'] = self._iter
        self.values['Salt'] = self._salt

        if 'SaltedPassword' not in self.values:
            self.check_values(['password'])
            password = bytes(self.values['password'])
            salted_pass = self.Hi(password, self._salt, self._iter)
            self.values['SaltedPassword'] = salted_pass

        salted_pass = self.values['SaltedPassword']
        client_key = self.HMAC(salted_pass, b'Client Key')
        stored_key = self.H(client_key)
        client_sig = self.HMAC(stored_key, self._soup)
        client_proof = XOR(client_key, client_sig)
        r += b',p=' + b64encode(client_proof).replace(b'\n', b'')
        server_key = self.HMAC(self.values['SaltedPassword'], b'Server Key')
        self.server_sig = self.HMAC(server_key, self._soup)
        return r

    def process_three(self, challenge=None):
        """
        """
        data = parse_challenge(challenge)
        if b64decode(data[b'v']) == self.server_sig:
            self._rspauth = True

    def okay(self):
        """
        """
        return self._rspauth

    def get_user(self):
        return self.values['username']


register_mechanism('SCRAM-', 60, SCRAM_HMAC)
register_mechanism('SCRAM-', 70, SCRAM_HMAC, extra='-PLUS')
