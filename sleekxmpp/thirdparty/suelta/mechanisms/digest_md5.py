import sys

import random

from sleekxmpp.thirdparty.suelta.util import hash, bytes, quote
from sleekxmpp.thirdparty.suelta.sasl import Mechanism, register_mechanism
from sleekxmpp.thirdparty.suelta.exceptions import SASLError, SASLCancelled



def parse_challenge(stuff):
    """
    """
    ret = {}
    var = b''
    val = b''
    in_var = True
    in_quotes = False
    new = False
    escaped = False
    for c in stuff:
        if sys.version_info >= (3, 0):
            c = bytes([c])
        if in_var:
            if c.isspace():
                continue
            if c == b'=':
                in_var = False
                new = True
            else:
                var += c
        else:
            if new:
                if c == b'"':
                    in_quotes = True
                else:
                    val += c
                new = False
            elif in_quotes:
                if escaped:
                    escaped = False
                    val += c
                else:
                    if c == b'\\':
                        escaped = True
                    elif c == b'"':
                        in_quotes = False
                    else:
                        val += c
            else:
                if c == b',':
                    if var:
                        ret[var] = val
                    var = b''
                    val = b''
                    in_var = True
                else:
                    val += c
    if var:
        ret[var] = val
    return ret


class DIGEST_MD5(Mechanism):

    """
    """

    enc_magic = 'Digest session key to client-to-server signing key magic'
    dec_magic = 'Digest session key to server-to-client signing key magic'

    def __init__(self, sasl, name):
        """
        """
        super(DIGEST_MD5, self).__init__(sasl, name, 3)

        self.hash = hash(name[7:])
        if self.hash is None:
            raise SASLCancelled(self.sasl, self)

        if not self.sasl.tls_active():
            if not self.sasl.sec_query(self, '-ENCRYPTION, DIGEST-MD5'):
                raise SASLCancelled(self.sasl, self)

        self._rspauth_okay = False
        self._digest_uri = None
        self._a1 = None
        self._enc_buf = b''
        self._enc_key = None
        self._enc_seq = 0
        self._max_buffer = 65536
        self._dec_buf = b''
        self._dec_key = None
        self._dec_seq = 0
        self._qops = [b'auth']
        self._qop = b'auth'

    def MAC(self, seq, msg, key):
        """
        """
        mac = hmac.HMAC(key=key, digestmod=self.hash)
        seqnum = num_to_bytes(seq)
        mac.update(seqnum)
        mac.update(msg)
        return mac.digest()[:10] + b'\x00\x01' + seqnum


    def encode(self, text):
        """
        """
        self._enc_buf += text

    def flush(self):
        """
        """
        result = b''
        # Leave buffer space for the MAC
        mbuf = self._max_buffer - 10 - 2 - 4

        while self._enc_buf:
            msg = self._encbuf[:mbuf]
            mac = self.MAC(self._enc_seq, msg, self._enc_key, self.hash)
            self._enc_seq += 1
            msg += mac
            result += num_to_bytes(len(msg)) + msg
            self._enc_buf = self._enc_buf[mbuf:]

        return result

    def decode(self, text):
        """
        """
        self._dec_buf += text
        result = b''

        while len(self._dec_buf) > 4:
            num = bytes_to_num(self._dec_buf)
            if len(self._dec_buf) < (num + 4):
                return result

            mac = self._dec_buf[4:4 + num]
            self._dec_buf = self._dec_buf[4 + num:]
            msg = mac[:-16]

            mac_conf = self.MAC(self._dec_mac, msg, self._dec_key)
            if mac[-16:] != mac_conf:
                self._desc_sec = None
                return result

            self._dec_seq += 1
            result += msg

        return result

    def response(self):
        """
        """
        vitals = ['username']
        if not self.has_values(['key_hash']):
            vitals.append('password')
        self.check_values(vitals)

        resp = {}
        if 'auth-int' in self._qops:
            self._qop = b'auth-int'
        resp['qop'] = self._qop
        if 'realm' in self.values:
            resp['realm'] = quote(self.values['realm'])

        resp['username'] = quote(bytes(self.values['username']))
        resp['nonce'] = quote(self.values['nonce'])
        if self.values['nc']:
            self._cnonce = self.values['cnonce']
        else:
            self._cnonce = bytes('%s' % random.random())[2:]
        resp['cnonce'] = quote(self._cnonce)
        self.values['nc'] += 1
        resp['nc'] = bytes('%08x' % self.values['nc'])

        service = bytes(self.sasl.service)
        host = bytes(self.sasl.host)
        self._digest_uri = service + b'/' + host
        resp['digest-uri'] = quote(self._digest_uri)

        a2 = b'AUTHENTICATE:' + self._digest_uri
        if self._qop != b'auth':
            a2 += b':00000000000000000000000000000000'
            resp['maxbuf'] = b'16777215'  # 2**24-1
        resp['response'] = self.gen_hash(a2)
        return b','.join([bytes(k) + b'=' + bytes(v) for k, v in resp.items()])

    def gen_hash(self, a2):
        """
        """
        if not self.has_values(['key_hash']):
            key_hash = self.hash()
            user = bytes(self.values['username'])
            password = bytes(self.values['password'])
            realm = bytes(self.values['realm'])
            kh = user + b':' + realm + b':' + password
            key_hash.update(kh)
            self.values['key_hash'] = key_hash.digest()

        a1 = self.hash(self.values['key_hash'])
        a1h = b':' + self.values['nonce'] + b':' + self._cnonce
        a1.update(a1h)
        response = self.hash()
        self._a1 = a1.digest()
        rv = bytes(a1.hexdigest().lower())
        rv += b':' + self.values['nonce']
        rv += b':' + bytes('%08x' % self.values['nc'])
        rv += b':' + self._cnonce
        rv += b':' + self._qop
        rv += b':' + bytes(self.hash(a2).hexdigest().lower())
        response.update(rv)
        return bytes(response.hexdigest().lower())

    def mutual_auth(self, cmp_hash):
        """
        """
        a2 = b':' + self._digest_uri
        if self._qop != b'auth':
            a2 += b':00000000000000000000000000000000'
        if self.gen_hash(a2) == cmp_hash:
            self._rspauth_okay = True

    def prep(self):
        """
        """
        if 'password' in self.values:
            del self.values['password']
        self.values['cnonce'] = self._cnonce

    def process(self, challenge=None):
        """
        """
        if challenge is None:
            if self.has_values(['username', 'realm', 'nonce', 'key_hash',
                                'nc', 'cnonce', 'qops']):
                self._qops = self.values['qops']
                return self.response()
            else:
                return None

        d = parse_challenge(challenge)
        if b'rspauth' in d:
            self.mutual_auth(d[b'rspauth'])
        else:
            if b'realm' not in d:
                d[b'realm'] = self.sasl.def_realm
            for key in ['nonce', 'realm']:
                if bytes(key) in d:
                    self.values[key] = d[bytes(key)]
            self.values['nc'] = 0
            self._qops = [b'auth']
            if b'qop' in d:
                self._qops = [x.strip() for x in d[b'qop'].split(b',')]
            self.values['qops'] = self._qops
            if b'maxbuf' in d:
                self._max_buffer = int(d[b'maxbuf'])
            return self.response()

    def okay(self):
        """
        """
        if self._rspauth_okay and self._qop == b'auth-int':
            self._enc_key = self.hash(self._a1 + self.enc_magic).digest()
            self._dec_key = self.hash(self._a1 + self.dec_magic).digest()
            self.encoding = True
        return self._rspauth_okay


register_mechanism('DIGEST-', 30, DIGEST_MD5)
