from sleekxmpp.thirdparty.suelta.util import hashes
from sleekxmpp.thirdparty.suelta.saslprep import saslprep

#: Global session storage for user answers to requested mechanism values
#: and security questions. This allows the user's preferences to be
#: persisted across multiple SASL authentication attempts made by the
#: same process.
SESSION = {'answers': {},
           'passwords': {},
           'sec_queries': {},
           'stash': {},
           'stash_file': ''}

#: Global registry mapping mechanism names to implementation classes.
MECHANISMS = {}

#: Global registry mapping mechanism names to security scores.
MECH_SEC_SCORES = {}


def register_mechanism(basename, basescore, impl, extra=None, use_hashes=True):
    """
    Add a SASL mechanism to the registry of available mechanisms.

    :param basename: The base name of the mechanism type, such as ``CRAM-``.
    :param basescore: The base security score for this type of mechanism.
    :param impl: The class implementing the mechanism.
    :param extra: Any additional qualifiers to the mechanism name,
                  such as ``-PLUS``.
    :param use_hashes: If ``True``, then register the mechanism for use with
                       all available hashes.
    """
    n = 0
    if use_hashes:
        for hashing_alg in hashes():
            n += 1
            name = basename + hashing_alg
            if extra is not None:
                name += extra
            MECHANISMS[name] = impl
            MECH_SEC_SCORES[name] = basescore + n
    else:
        MECHANISMS[basename] = impl
        MECH_SEC_SCORES[basename] = basescore


def set_stash_file(filename):
    """
    Enable or disable storing the stash to disk.

    If the filename is ``None``, then disable using a stash file.

    :param filename: The path to the file to store the stash data.
    """
    SESSION['stash_file'] = filename
    try:
        import marshal
        stash_file = file(filename)
        SESSION['stash'] = marshal.load(stash_file)
    except:
        SESSION['stash'] = {}


def sec_query_allow(mech, query):
    """
    Quick default to allow all feature combinations which could
    negatively affect security.

    :param mech: The chosen SASL mechanism
    :param query: An encoding of the combination of enabled and
                  disabled features which may affect security.

    :returns: ``True``
    """
    return True


class SASL(object):

    """
    """

    def __init__(self, host, service, mech=None, username=None,
                 min_sec=0, request_values=None, sec_query=None,
                 tls_active=None, def_realm=None):
        """
        :param string host: The host of the service requiring authentication.
        :param string service: The name of the underlying protocol in use.
        :param string mech: Optional name of the SASL mechanism to use.
                            If given, only this mechanism may be used for
                            authentication.
        :param string username: The username to use when authenticating.
        :param request_values: Reference to a function for supplying
                               values requested by mechanisms, such
                               as passwords. (See above)
        :param sec_query: Reference to a function for approving or
                          denying feature combinations which could
                          negatively impact security. (See above)
        :param tls_active: Function for indicating if TLS has been
                           negotiated. (See above)
        :param integer min_sec: The minimum security level accepted. This
                                only allows for SASL mechanisms whose
                                security rating is greater than `min_sec`.
        :param string def_realm: The default realm, if different than `host`.

        :type request_values: :func:`request_values`
        :type sec_query: :func:`sec_query`
        :type tls_active: :func:`tls_active`
        """
        self.host = host
        self.def_realm = def_realm or host
        self.service = service
        self.user = username
        self.mech = mech
        self.min_sec = min_sec - 1

        self.request_values = request_values
        self._sec_query = sec_query
        if tls_active is not None:
            self.tls_active = tls_active
        else:
            self.tls_active = lambda: False

        self.try_username = self.user
        self.try_password = None

        self.stash_id = None
        self.testkey = None

    def reset_stash_id(self, username):
        """
        Reset the ID for the stash for persisting user data.

        :param username: The username to base the new ID on.
        """
        username = saslprep(username)
        self.user = username
        self.try_username = self.user
        self.testkey = [self.user, self.host, self.service]
        self.stash_id = '\0'.join(self.testkey)

    def sec_query(self, mech, query):
        """
        Request authorization from the user to use a combination
        of features which could negatively affect security.

        The ``sec_query`` callback when creating the SASL object will
        be called if the query has not been answered before. Otherwise,
        the query response will be pulled from ``SESSION['sec_queries']``.

        If no ``sec_query`` callback was provided, then all queries
        will be denied.

        :param mech: The chosen SASL mechanism
        :param query: An encoding of the combination of enabled and
                      disabled features which may affect security.
        :rtype: bool
        """
        if self._sec_query is None:
            return False
        if query in SESSION['sec_queries']:
            return SESSION['sec_queries'][query]
        resp = self._sec_query(mech, query)
        if resp:
            SESSION['sec_queries'][query] = resp

        return resp

    def find_password(self, mech):
        """
        Find and return the user's password, if it has been entered before
        during this session.

        :param mech: The chosen SASL mechanism.
        """
        if self.try_password is not None:
            return self.try_password
        if self.testkey is None:
            return

        testkey = self.testkey[:]
        lockout = 1

    def find_username(self):
        """Find and return user's username if known."""
        return self.try_username

    def success(self, mech):
        mech.preprep()
        if 'password' in mech.values:
            testkey = self.testkey[:]
            while len(testkey):
                tk = '\0'.join(testkey)
                if tk in SESSION['passwords']:
                    break
                SESSION['passwords'][tk] = mech.values['password']
                testkey = testkey[:-1]
        mech.prep()
        mech.save_values()

    def failure(self, mech):
        mech.clear()
        self.testkey = self.testkey[:-1]

    def choose_mechanism(self, mechs, force_plain=False):
        """
        Choose the most secure mechanism from a list of mechanisms.

        If ``force_plain`` is given, return the ``PLAIN`` mechanism.

        :param mechs: A list of mechanism names.
        :param force_plain: If ``True``, force the selection of the
                            ``PLAIN`` mechanism.
        :returns: A SASL mechanism object, or ``None`` if no mechanism
                  could be selected.
        """
        # Handle selection of PLAIN and ANONYMOUS
        if force_plain:
            return MECHANISMS['PLAIN'](self, 'PLAIN')

        if self.user is not None:
            requested_mech = '*' if self.mech is None else self.mech
        else:
            if self.mech is None:
                requested_mech = 'ANONYMOUS'
            else:
                requested_mech = self.mech
        if requested_mech == '*' and self.user in ['', 'anonymous', None]:
            requested_mech = 'ANONYMOUS'

        # If a specific mechanism was requested, try it
        if requested_mech != '*':
            if requested_mech in MECHANISMS and \
               requested_mech in MECH_SEC_SCORES:
                return MECHANISMS[requested_mech](self, requested_mech)
            return None

        # Pick the best mechanism based on its security score
        best_score = self.min_sec
        best_mech = None
        for name in mechs:
            if name in MECH_SEC_SCORES:
                if MECH_SEC_SCORES[name] > best_score:
                    best_score = MECH_SEC_SCORES[name]
                    best_mech = name
        if best_mech is not None:
            best_mech = MECHANISMS[best_mech](self, best_mech)

        return best_mech


class Mechanism(object):

    """
    """

    def __init__(self, sasl, name, version=0, use_stash=True):
        self.name = name
        self.sasl = sasl
        self.use_stash = use_stash

        self.encoding = False
        self.values = {}

        if use_stash:
            self.load_values()

    def load_values(self):
        """Retrieve user data from the stash."""
        self.values = {}
        if not self.use_stash:
            return False
        if self.sasl.stash_id is not None:
            if self.sasl.stash_id in SESSION['stash']:
                if SESSION['stash'][self.sasl.stash_id]['mech'] == self.name:
                    values = SESSION['stash'][self.sasl.stash_id]['values']
                    self.values.update(values)
        if self.sasl.user is not None:
            if not self.has_values(['username']):
                self.values['username'] = self.sasl.user
        return None

    def save_values(self):
        """
        Save user data to the session stash.

        If a stash file name has been set using ``SESSION['stash_file']``,
        the saved values will be persisted to disk.
        """
        if not self.use_stash:
            return False
        if self.sasl.stash_id is not None:
            if self.sasl.stash_id not in SESSION['stash']:
                SESSION['stash'][self.sasl.stash_id] = {}
            SESSION['stash'][self.sasl.stash_id]['values'] = self.values
            SESSION['stash'][self.sasl.stash_id]['mech'] = self.name
            if SESSION['stash_file'] not in ['', None]:
                import marshal
                stash_file = file(SESSION['stash_file'], 'wb')
                marshal.dump(SESSION['stash'], stash_file)

    def clear(self):
        """Reset all user data, except the username."""
        username = None
        if 'username' in self.values:
            username = self.values['username']
        self.values = {}
        if username is not None:
            self.values['username'] = username
        self.save_values()
        self.values = {}
        self.load_values()

    def okay(self):
        """
        Indicate if mutual authentication has completed successfully.

        :rtype: bool
        """
        return False

    def preprep(self):
        """Ensure that the stash ID has been set before processing."""
        if self.sasl.stash_id is None:
            if 'username' in self.values:
                self.sasl.reset_stash_id(self.values['username'])

    def prep(self):
        """
        Prepare stored values for processing.

        For example, by removing extra copies of passwords from memory.
        """
        pass

    def process(self, challenge=None):
        """
        Process a challenge request and return the response.

        :param challenge: A challenge issued by the server that
                          must be answered for authentication.
        """
        raise NotImplemented

    def fulfill(self, values):
        """
        Provide requested values to the mechanism.

        :param values: A dictionary of requested values.
        """
        if 'password' in values:
            values['password'] = saslprep(values['password'])
        self.values.update(values)

    def missing_values(self, keys):
        """
        Return a dictionary of value names that have not been given values
        by the user, or retrieved from the stash.

        :param keys: A list of value names to check.
        :rtype: dict
        """
        vals = {}
        for name in keys:
            if name not in self.values or self.values[name] is None:
                if self.use_stash:
                    if name == 'username':
                        value = self.sasl.find_username()
                        if value is not None:
                            self.sasl.reset_stash_id(value)
                            self.values[name] = value
                            break
                    if name == 'password':
                        value = self.sasl.find_password(self)
                        if value is not None:
                            self.values[name] = value
                            break
                vals[name] = None
        return vals

    def has_values(self, keys):
        """
        Check that the given values have been retrieved from the user,
        or from the stash.

        :param keys: A list of value names to check.
        """
        return len(self.missing_values(keys)) == 0

    def check_values(self, keys):
        """
        Request missing values from the user.

        :param keys: A list of value names to request, if missing.
        """
        vals = self.missing_values(keys)
        if vals:
            self.sasl.request_values(self, vals)

    def get_user(self):
        """Return the username usd for this mechanism."""
        return self.values['username']
