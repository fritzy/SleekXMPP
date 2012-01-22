import sys
import logging
try:
    from httplib import HTTPSConnection
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
    from http.client import HTTPSConnection

from sleekxmpp.thirdparty.suelta.util import bytes
from sleekxmpp.thirdparty.suelta.sasl import Mechanism, register_mechanism
from sleekxmpp.thirdparty.suelta.exceptions import SASLError, SASLCancelled


log = logging.getLogger(__name__)


class X_GOOGLE_TOKEN(Mechanism):

    def __init__(self, sasl, name):
        super(X_GOOGLE_TOKEN, self).__init__(sasl, name)
        self.check_values(['email', 'password', 'access_token'])

    def process(self, challenge=None):
        if not self.values.get('access_token', False):
            log.debug("SASL: Requesting auth token from Google")
            try:
                conn = HTTPSConnection('www.google.com')
            except:
                raise SASLError(self.sasl, 'Could not connect to Google')
            params = urlencode({
                'accountType': 'GOOGLE',
                'service': 'mail',
                'Email': self.values['email'],
                'Passwd': self.values['password']
            })
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded' 
            }
            try:
                conn.request('POST', '/accounts/ClientLogin', params, headers)
                resp = conn.getresponse().read()
                data = {}
                for line in resp.split():
                    k, v = line.split(b'=', 1)
                    data[k] = v
            except Exception as e:
                raise e
                #raise SASLError(self.sasl, 'Could not retrieve login data')

            if b'SID' not in data:
                raise SASLError(self.sasl, 'Required data not found')

            params = urlencode({
                'SID': data[b'SID'],
                'LSID': data[b'LSID'],
                'service': 'mail'
            })
            try:
                conn.request('POST', '/accounts/IssueAuthToken', params, headers)
                resp = conn.getresponse()
                data = resp.read().split()
            except:
                raise SASLError(self.sasl, 'Could not retrieve auth data')
            if not data:
                raise SASLError(self.sasl, 'Could not retrieve token')

            self.values['access_token'] = data[0]
 
        email = bytes(self.values['email'])
        token = bytes(self.values['access_token'])
        return b'\x00' + email + b'\x00' + token

    def okay(self):
        return True


register_mechanism('X-GOOGLE-TOKEN', 3, X_GOOGLE_TOKEN, use_hashes=False)
