from sleekxmpp.thirdparty.suelta.util import bytes
from sleekxmpp.thirdparty.suelta.sasl import Mechanism, register_mechanism

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse



class X_FACEBOOK_PLATFORM(Mechanism):

    def __init__(self, sasl, name):
        super(X_FACEBOOK_PLATFORM, self).__init__(sasl, name)
        self.check_values(['access_token', 'api_key'])

    def process(self, challenge=None):
        if challenge is not None:
            values = {}
            for kv in challenge.split(b'&'):
                key, value = kv.split(b'=')
                values[key] = value

            resp_data = {
                'method': values[b'method'],
                'v': '1.0',
                'call_id': '1.0',
                'nonce': values[b'nonce'],
                'access_token': self.values['access_token'],
                'api_key': self.values['api_key']
            }
            
            for k, v in resp_data.items():
                resp_data[k] = bytes(v).decode('utf-8')

            resp = '&'.join(['%s=%s' % (k, v) for k, v in resp_data.items()])
            return bytes(resp)
        return b''

    def okay(self):
        return True

register_mechanism('X-FACEBOOK-PLATFORM', 40, X_FACEBOOK_PLATFORM, use_hashes=False)
