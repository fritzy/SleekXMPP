"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from __future__ import absolute_import, unicode_literals

import logging
import base64
import sys
import hashlib
import random
import threading

from sleekxmpp import plugins
from sleekxmpp import stanza
from sleekxmpp.basexmpp import BaseXMPP
from sleekxmpp.stanza import *
from sleekxmpp.stanza import tls
from sleekxmpp.stanza import sasl
from sleekxmpp.xmlstream import XMLStream, RestartStream
from sleekxmpp.xmlstream import StanzaBase, ET, register_stanza_plugin
from sleekxmpp.xmlstream.matcher import *
from sleekxmpp.xmlstream.handler import *

# Flag indicating if DNS SRV records are available for use.
SRV_SUPPORT = True
try:
    import dns.resolver
except:
    SRV_SUPPORT = False


log = logging.getLogger(__name__)


class ClientXMPP(BaseXMPP):

    """
    SleekXMPP's client class.

    Use only for good, not for evil.

    Attributes:

    Methods:
        connect          -- Overrides XMLStream.connect.
        del_roster_item  -- Delete a roster item.
        get_roster       -- Retrieve the roster from the server.
        register_feature -- Register a stream feature.
        update_roster    -- Update a roster item.
    """

    def __init__(self, jid, password, ssl=False, plugin_config={},
                 plugin_whitelist=[], escape_quotes=True):
        """
        Create a new SleekXMPP client.

        Arguments:
            jid              -- The JID of the XMPP user account.
            password         -- The password for the XMPP user account.
            ssl              -- Deprecated.
            plugin_config    -- A dictionary of plugin configurations.
            plugin_whitelist -- A list of approved plugins that will be loaded
                                when calling register_plugins.
            escape_quotes    -- Deprecated.
        """
        BaseXMPP.__init__(self, 'jabber:client')

        # To comply with PEP8, method names now use underscores.
        # Deprecated method names are re-mapped for backwards compatibility.
        self.updateRoster = self.update_roster
        self.delRosterItem = self.del_roster_item
        self.getRoster = self.get_roster
        self.registerFeature = self.register_feature

        self.set_jid(jid)
        self.password = password
        self.escape_quotes = escape_quotes
        self.plugin_config = plugin_config
        self.plugin_whitelist = plugin_whitelist
        self.srv_support = SRV_SUPPORT

        self.session_started_event = threading.Event()
        self.session_started_event.clear()

        self.stream_header = "<stream:stream to='%s' %s %s version='1.0'>" % (
                self.boundjid.host,
                "xmlns:stream='%s'" % self.stream_ns,
                "xmlns='%s'" % self.default_ns)
        self.stream_footer = "</stream:stream>"

        self.features = []
        self._stream_feature_handlers = {}
        self._stream_feature_order = []
        self._sasl_mechanism_handlers = {}
        self._sasl_mechanism_priorities = []

        #TODO: Use stream state here
        self.authenticated = False
        self.sessionstarted = False
        self.bound = False
        self.bindfail = False

        self.add_event_handler('connected', self._handle_connected)

        self.register_stanza(StreamFeatures)
        self.register_stanza(tls.Proceed)
        self.register_stanza(sasl.Success)
        self.register_stanza(sasl.Failure)
        self.register_stanza(sasl.Auth)

        self.register_handler(
                Callback('Stream Features',
                         MatchXPath('{%s}features' % self.stream_ns),
                         self._handle_stream_features))
        self.register_handler(
                Callback('Roster Update',
                         MatchXPath('{%s}iq/{%s}query' % (
                             self.default_ns,
                             'jabber:iq:roster')),
                         self._handle_roster))

        self.register_feature('starttls', self._handle_starttls,
                              restart=True,
                              order=0)
        self.register_feature('mechanisms', self._handle_sasl_auth,
                              restart=True,
                              order=100)
        self.register_feature('bind', self._handle_bind_resource,
                              restart=False,
                              order=10000)
        self.register_feature('session', self._handle_start_session,
                              restart=False,
                              order=10001)

        self.register_sasl_mechanism('PLAIN',
                                     self._handle_sasl_plain,
                                     priority=1)
        self.register_sasl_mechanism('ANONYMOUS',
                                     self._handle_sasl_plain,
                                     priority=0)

    def connect(self, address=tuple(), reattempt=True):
        """
        Connect to the XMPP server.

        When no address is given, a SRV lookup for the server will
        be attempted. If that fails, the server user in the JID
        will be used.

        Arguments:
            address   -- A tuple containing the server's host and port.
            reattempt -- If True, reattempt the connection if an
                         error occurs.
        """
        self.session_started_event.clear()
        if not address or len(address) < 2:
            if not self.srv_support:
                log.debug("Did not supply (address, port) to connect" + \
                              " to and no SRV support is installed" + \
                              " (http://www.dnspython.org)." + \
                              " Continuing to attempt connection, using" + \
                              " server hostname from JID.")
            else:
                log.debug("Since no address is supplied," + \
                              "attempting SRV lookup.")
                try:
                    xmpp_srv = "_xmpp-client._tcp.%s" % self.boundjid.host
                    answers = dns.resolver.query(xmpp_srv, dns.rdatatype.SRV)
                except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                    log.debug("No appropriate SRV record found." + \
                                  " Using JID server name.")
                except (dns.exception.Timeout,):
                    log.debug("DNS resolution timed out.")
                else:
                    # Pick a random server, weighted by priority.

                    addresses = {}
                    intmax = 0
                    for answer in answers:
                        intmax += answer.priority
                        addresses[intmax] = (answer.target.to_text()[:-1],
                                             answer.port)
                    #python3 returns a generator for dictionary keys
                    priorities = [x for x in addresses.keys()]
                    priorities.sort()

                    picked = random.randint(0, intmax)
                    for priority in priorities:
                        if picked <= priority:
                            address = addresses[priority]
                            break

        if not address:
            # If all else fails, use the server from the JID.
            address = (self.boundjid.host, 5222)

        return XMLStream.connect(self, address[0], address[1],
                                 use_tls=True, reattempt=reattempt)

    def register_feature(self, name, handler, restart=False, order=5000):
        """
        Register a stream feature.

        Arguments:
            name    -- The name of the stream feature.
            handler -- The function to execute if the feature is received.
            restart -- Indicates if feature processing should halt with
                       this feature. Defaults to False.
            order   -- The relative ordering in which the feature should
                       be negotiated. Lower values will be attempted
                       earlier when available.
        """
        self._stream_feature_handlers[name] = (handler, restart)
        self._stream_feature_order.append((order, name))
        self._stream_feature_order.sort()

    def register_sasl_mechanism(self, name, handler, priority=0):
        """
        Register a handler for a SASL authentication mechanism.

        Arguments:
            name     -- The name of the mechanism (all caps)
            handler  -- The function that will perform the
                        authentication. The function must
                        return True if it is able to carry
                        out the authentication, False if
                        a required condition is not met.
            priority -- An integer value indicating the
                        preferred ordering for the mechanism.
                        High values will be attempted first.
        """
        self._sasl_mechanism_handlers[name] = handler
        self._sasl_mechanism_priorities.append((priority, name))
        self._sasl_mechanism_priorities.sort(reverse=True)

    def remove_sasl_mechanism(self, name):
        """
        Remove support for a given SASL authentication mechanism.

        Arguments:
            name -- The name of the mechanism to remove (all caps)
        """
        if name in self._sasl_mechanism_handlers:
            del self._sasl_mechanism_handlers[name]

        p = self._sasl_mechanism_priorities
        self._sasl_mechanism_priorities = [i for i in p if i[1] != name]

    def update_roster(self, jid, name=None, subscription=None, groups=[]):
        """
        Add or change a roster item.

        Arguments:
            jid          -- The JID of the entry to modify.
            name         -- The user's nickname for this JID.
            subscription -- The subscription status. May be one of
                            'to', 'from', 'both', or 'none'. If set
                            to 'remove', the entry will be deleted.
            groups       -- The roster groups that contain this item.
        """
        iq = self.Iq()
        iq['type'] = 'set'
        iq['roster']['items'] = {jid: {'name': name,
                                       'subscription': subscription,
                                       'groups': groups}}
        response = iq.send()
        return response['type'] == 'result'

    def del_roster_item(self, jid):
        """
        Remove an item from the roster by setting its subscription
        status to 'remove'.

        Arguments:
            jid -- The JID of the item to remove.
        """
        return self.update_roster(jid, subscription='remove')

    def get_roster(self):
        """Request the roster from the server."""
        iq = self.Iq()
        iq['type'] = 'get'
        iq.enable('roster')
        response = iq.send()
        self._handle_roster(response, request=True)

    def _handle_connected(self, event=None):
        #TODO: Use stream state here
        self.authenticated = False
        self.sessionstarted = False
        self.bound = False
        self.bindfail = False
        self.features = []

        def session_timeout():
            if not self.session_started_event.isSet():
                log.debug("Session start has taken more than 15 seconds")
                self.disconnect(reconnect=self.auto_reconnect)

        self.schedule("session timeout checker", 15, session_timeout)

    def _handle_stream_features(self, features):
        """
        Process the received stream features.

        Arguments:
            features -- The features stanza.
        """
        for order, name in self._stream_feature_order:
            if name in features['features']:
                handler, restart = self._stream_feature_handlers[name]
                if handler(features) and restart:
                    # Don't continue if the feature requires
                    # restarting the XML stream.
                    return True

    def _handle_starttls(self, features):
        """
        Handle notification that the server supports TLS.

        Arguments:
            features -- The stream:features element.
        """

        def tls_proceed(proceed):
            """Restart the XML stream when TLS is accepted."""
            log.debug("Starting TLS")
            if self.start_tls():
                self.features.append('starttls')
                raise RestartStream()

        if self.ssl_support:
            self.register_handler(
                    Callback('STARTTLS Proceed',
                            MatchXPath(tls.Proceed.tag_name()),
                            tls_proceed,
                            instream=True))
            self.send(features['starttls'])
            return True
        else:
            log.warning("The module tlslite is required to log in" +\
                            " to some servers, and has not been found.")
            return False

    def _handle_sasl_auth(self, features):
        """
        Handle authenticating using SASL.

        Arguments:
            features -- The stream features stanza.
        """

        def sasl_success(stanza):
            """SASL authentication succeeded. Restart the stream."""
            self.authenticated = True
            self.features.append('mechanisms')
            raise RestartStream()

        def sasl_fail(stanza):
            """SASL authentication failed. Disconnect and shutdown."""
            log.info("Authentication failed.")
            self.event("failed_auth", direct=True)
            self.disconnect()
            log.debug("Starting SASL Auth")
            return True

        self.register_handler(
                Callback('SASL Success',
                         MatchXPath(sasl.Success.tag_name()),
                         sasl_success,
                         instream=True,
                         once=True))

        self.register_handler(
                Callback('SASL Failure',
                         MatchXPath(sasl.Failure.tag_name()),
                         sasl_fail,
                         instream=True,
                         once=True))

        for priority, mech in self._sasl_mechanism_priorities:
            if mech in self._sasl_mechanism_handlers:
                handler = self._sasl_mechanism_handlers[mech]
                if handler(self):
                    break
        else:
            log.error("No appropriate login method.")
            self.disconnect()

        return True

    def _handle_sasl_plain(self, xmpp):
        """
        Attempt to authenticate using SASL PLAIN.

        Arguments:
            xmpp -- The SleekXMPP connection instance.
        """
        if not xmpp.boundjid.user:
            return False

        if sys.version_info < (3, 0):
            user = bytes(self.boundjid.user)
            password = bytes(self.password)
        else:
            user = bytes(self.boundjid.user, 'utf-8')
            password = bytes(self.password, 'utf-8')

        auth = base64.b64encode(b'\x00' + user + \
                                b'\x00' + password).decode('utf-8')

        resp = sasl.Auth(xmpp)
        resp['mechanism'] = 'PLAIN'
        resp['value'] = auth
        resp.send()

        return True

    def _handle_sasl_anonymous(self, xmpp):
        """
        Attempt to authenticate using SASL ANONYMOUS.

        Arguments:
            xmpp -- The SleekXMPP connection instance.
        """
        if xmpp.boundjid.user:
            return False

        resp = sasl.Auth(xmpp)
        resp['mechanism'] = 'ANONYMOUS'
        resp.send()

        return True

    def _handle_bind_resource(self, features):
        """
        Handle requesting a specific resource.

        Arguments:
            features -- The stream features stanza.
        """
        log.debug("Requesting resource: %s" % self.boundjid.resource)
        iq = self.Iq()
        iq['type'] = 'set'
        iq.enable('bind')
        if self.boundjid.resource:
            iq['bind']['resource'] = self.boundjid.resource
        response = iq.send()

        self.set_jid(response['bind']['jid'])
        self.bound = True

        log.info("Node set to: %s" % self.boundjid.full)

        if 'session' not in features['features']:
            log.debug("Established Session")
            self.sessionstarted = True
            self.session_started_event.set()
            self.event("session_start")

    def _handle_start_session(self, features):
        """
        Handle the start of the session.

        Arguments:
            feature -- The stream features element.
        """
        iq = self.Iq()
        iq['type'] = 'set'
        iq.enable('session')
        response = iq.send()

        log.debug("Established Session")
        self.sessionstarted = True
        self.session_started_event.set()
        self.event("session_start")

    def _handle_roster(self, iq, request=False):
        """
        Update the roster after receiving a roster stanza.

        Arguments:
            iq      -- The roster stanza.
            request -- Indicates if this stanza is a response
                       to a request for the roster.
        """
        if iq['type'] == 'set' or (iq['type'] == 'result' and request):
            for jid in iq['roster']['items']:
                if not jid in self.roster:
                    self.roster[jid] = {'groups': [],
                                        'name': '',
                                        'subscription': 'none',
                                        'presence': {},
                                        'in_roster': True}
                self.roster[jid].update(iq['roster']['items'][jid])

        self.event("roster_update", iq)
        if iq['type'] == 'set':
            iq.reply()
            iq.enable('roster')
            iq.send()
