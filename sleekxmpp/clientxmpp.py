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

import sleekxmpp
from sleekxmpp import plugins
from sleekxmpp import stanza
from sleekxmpp import features
from sleekxmpp.basexmpp import BaseXMPP
from sleekxmpp.stanza import *
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

        self.set_jid(jid)
        self.password = password
        self.escape_quotes = escape_quotes
        self.plugin_config = plugin_config
        self.plugin_whitelist = plugin_whitelist
        self.srv_support = SRV_SUPPORT

        self.stream_header = "<stream:stream to='%s' %s %s version='1.0'>" % (
                self.boundjid.host,
                "xmlns:stream='%s'" % self.stream_ns,
                "xmlns='%s'" % self.default_ns)
        self.stream_footer = "</stream:stream>"

        self.features = []
        self._stream_feature_handlers = {}
        self._stream_feature_order = []

        #TODO: Use stream state here
        self.authenticated = False
        self.sessionstarted = False
        self.bound = False
        self.bindfail = False

        self.add_event_handler('connected', self._handle_connected)

        self.register_stanza(StreamFeatures)

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

        # Setup default stream features
        self.register_plugin('feature_starttls')
        self.register_plugin('feature_mechanisms')
        self.register_plugin('feature_bind')
        self.register_plugin('feature_session')

        # Setup default SASL mechanisms
        self.register_plugin('sasl_plain',
                {'priority': 1})
        self.register_plugin('sasl_anonymous',
                {'priority': 0})

    def connect(self, address=tuple(), reattempt=True, use_tls=True):
        """
        Connect to the XMPP server.

        When no address is given, a SRV lookup for the server will
        be attempted. If that fails, the server user in the JID
        will be used.

        Arguments:
            address   -- A tuple containing the server's host and port.
            reattempt -- If True, reattempt the connection if an
                         error occurs. Defaults to True.
            use_tls   -- Indicates if TLS should be used for the
                         connection. Defaults to True.
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
                                 use_tls=use_tls, reattempt=reattempt)

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
        self['feature_mechanisms'].register_mechanism(name, handler, priority)

    def remove_sasl_mechanism(self, name):
        """
        Remove support for a given SASL authentication mechanism.

        Arguments:
            name -- The name of the mechanism to remove (all caps)
        """
        self['feature_mechanisms'].remove_mechanism(name)

    def update_roster(self, jid, name=None, subscription=None, groups=[],
                            block=True, timeout=None, callback=None):
        """
        Add or change a roster item.

        Arguments:
            jid          -- The JID of the entry to modify.
            name         -- The user's nickname for this JID.
            subscription -- The subscription status. May be one of
                            'to', 'from', 'both', or 'none'. If set
                            to 'remove', the entry will be deleted.
            groups       -- The roster groups that contain this item.
            block        -- Specify if the roster request will block
                            until a response is received, or a timeout
                            occurs. Defaults to True.
            timeout      -- The length of time (in seconds) to wait
                            for a response before continuing if blocking
                            is used. Defaults to self.response_timeout.
            callback     -- Optional reference to a stream handler function.
                            Will be executed when the roster is received.
                            Implies block=False.
        """
        iq = self.Iq()
        iq['type'] = 'set'
        iq['roster']['items'] = {jid: {'name': name,
                                       'subscription': subscription,
                                       'groups': groups}}
        response = iq.send(block, timeout, callback)
        if response in [False, None] or not isinstance(response, Iq):
            return response
        return response['type'] == 'result'

    def del_roster_item(self, jid):
        """
        Remove an item from the roster by setting its subscription
        status to 'remove'.

        Arguments:
            jid -- The JID of the item to remove.
        """
        return self.update_roster(jid, subscription='remove')

    def get_roster(self, block=True, timeout=None, callback=None):
        """
        Request the roster from the server.

        Arguments:
            block    -- Specify if the roster request will block until a
                        response is received, or a timeout occurs.
                        Defaults to True.
            timeout  -- The length of time (in seconds) to wait for a response
                        before continuing if blocking is used.
                        Defaults to self.response_timeout.
            callback -- Optional reference to a stream handler function. Will
                        be executed when the roster is received.
                        Implies block=False.
        """
        iq = self.Iq()
        iq['type'] = 'get'
        iq.enable('roster')
        response = iq.send(block, timeout, callback)

        if response == False:
            self.event('roster_timeout')

        if response in [False, None] or not isinstance(response, Iq):
            return response
        else:
            return self._handle_roster(response, request=True)

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
            self.event('roster_received', iq)

        self.event("roster_update", iq)
        if iq['type'] == 'set':
            iq.reply()
            iq.enable('roster')
            iq.send()
        return True


# To comply with PEP8, method names now use underscores.
# Deprecated method names are re-mapped for backwards compatibility.
ClientXMPP.updateRoster = ClientXMPP.update_roster
ClientXMPP.delRosterItem = ClientXMPP.del_roster_item
ClientXMPP.getRoster = ClientXMPP.get_roster
ClientXMPP.registerFeature = ClientXMPP.register_feature
