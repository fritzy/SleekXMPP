# -*- coding: utf-8 -*-
"""
    sleekxmpp.clientxmpp
    ~~~~~~~~~~~~~~~~~~~~

    This module provides XMPP functionality that
    is specific to client connections.

    Part of SleekXMPP: The Sleek XMPP Library

    :copyright: (c) 2011 Nathanael C. Fritz
    :license: MIT, see LICENSE for more details
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
try:
    import dns.resolver
except ImportError:
    DNSPYTHON = False
else:
    DNSPYTHON = True


log = logging.getLogger(__name__)


class ClientXMPP(BaseXMPP):

    """
    SleekXMPP's client class. (Use only for good, not for evil.)

    Typical use pattern:

    .. code-block:: python

        xmpp = ClientXMPP('user@server.tld/resource', 'password')
        # ... Register plugins and event handlers ...
        xmpp.connect()
        xmpp.process(block=False) # block=True will block the current
                                  # thread. By default, block=False

    :param jid: The JID of the XMPP user account.
    :param password: The password for the XMPP user account.
    :param ssl: **Deprecated.**
    :param plugin_config: A dictionary of plugin configurations.
    :param plugin_whitelist: A list of approved plugins that 
                    will be loaded when calling 
                    :meth:`~sleekxmpp.basexmpp.BaseXMPP.register_plugins()`.
    :param escape_quotes: **Deprecated.**
    """

    def __init__(self, jid, password, ssl=False, plugin_config={},
                 plugin_whitelist=[], escape_quotes=True, sasl_mech=None):
        BaseXMPP.__init__(self, jid, 'jabber:client')

        self.set_jid(jid)
        self.password = password
        self.escape_quotes = escape_quotes
        self.plugin_config = plugin_config
        self.plugin_whitelist = plugin_whitelist
        self.default_port = 5222

        self.stream_header = "<stream:stream to='%s' %s %s version='1.0'>" % (
                self.boundjid.host,
                "xmlns:stream='%s'" % self.stream_ns,
                "xmlns='%s'" % self.default_ns)
        self.stream_footer = "</stream:stream>"

        self.features = set()
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
        self.register_plugin('feature_bind')
        self.register_plugin('feature_session')
        self.register_plugin('feature_mechanisms',
                pconfig={'use_mech': sasl_mech} if sasl_mech else None)

    def connect(self, address=tuple(), reattempt=True,
                use_tls=True, use_ssl=False):
        """Connect to the XMPP server.

        When no address is given, a SRV lookup for the server will
        be attempted. If that fails, the server user in the JID
        will be used.

        :param address   -- A tuple containing the server's host and port.
        :param reattempt: If ``True``, repeat attempting to connect if an
                         error occurs. Defaults to ``True``.
        :param use_tls: Indicates if TLS should be used for the
                        connection. Defaults to ``True``.
        :param use_ssl: Indicates if the older SSL connection method
                        should be used. Defaults to ``False``.
        """
        self.session_started_event.clear()
        if not address:
            address = (self.boundjid.host, 5222)

        return XMLStream.connect(self, address[0], address[1],
                                 use_tls=use_tls, use_ssl=use_ssl,
                                 reattempt=reattempt)

    def get_dns_records(self, domain, port=None):
        """Get the DNS records for a domain, including SRV records.

        :param domain: The domain in question.
        :param port: If the results don't include a port, use this one.
        """
        if port is None:
            port = self.default_port
        if DNSPYTHON:
            try:
                record = "_xmpp-client._tcp.%s" % domain
                answers = []
                for answer in dns.resolver.query(record, dns.rdatatype.SRV):
                    address = (answer.target.to_text()[:-1], answer.port)
                    answers.append((address, answer.priority, answer.weight))
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                log.warning("No SRV records for %s", domain)
                answers = super(ClientXMPP, self).get_dns_records(domain, port)
            except dns.exception.Timeout:
                log.warning("DNS resolution timed out " + \
                            "for SRV record of %s", domain)
                answers = super(ClientXMPP, self).get_dns_records(domain, port)
            return answers
        else:
            log.warning("dnspython is not installed -- " + \
                        "relying on OS A record resolution")
            return [((domain, port), 0, 0)]

    def register_feature(self, name, handler, restart=False, order=5000):
        """Register a stream feature handler.

        :param name: The name of the stream feature.
        :param handler: The function to execute if the feature is received.
        :param restart: Indicates if feature processing should halt with
                        this feature. Defaults to ``False``.
        :param order: The relative ordering in which the feature should
                      be negotiated. Lower values will be attempted
                      earlier when available.
        """
        self._stream_feature_handlers[name] = (handler, restart)
        self._stream_feature_order.append((order, name))
        self._stream_feature_order.sort()

    def update_roster(self, jid, name=None, subscription=None, groups=[],
                            block=True, timeout=None, callback=None):
        """Add or change a roster item.

        :param jid: The JID of the entry to modify.
        :param name: The user's nickname for this JID.
        :param subscription: The subscription status. May be one of
                             ``'to'``, ``'from'``, ``'both'``, or
                             ``'none'``. If set to ``'remove'``,
                             the entry will be deleted.
        :param groups: The roster groups that contain this item.
        :param block: Specify if the roster request will block
                      until a response is received, or a timeout
                      occurs. Defaults to ``True``.
        :param timeout: The length of time (in seconds) to wait
                        for a response before continuing if blocking
                        is used. Defaults to 
            :attr:`~sleekxmpp.xmlstream.xmlstream.XMLStream.response_timeout`.
        :param callback: Optional reference to a stream handler function.
                         Will be executed when the roster is received.
                         Implies ``block=False``.
        """
        return self.client_roster.update(jid, name, subscription, groups,
                                         block, timeout, callback)

    def del_roster_item(self, jid):
        """Remove an item from the roster.
        
        This is done by setting its subscription status to ``'remove'``.

        :param jid: The JID of the item to remove.
        """
        return self.client_roster.remove(jid)

    def get_roster(self, block=True, timeout=None, callback=None):
        """Request the roster from the server.

        :param block: Specify if the roster request will block until a
                      response is received, or a timeout occurs.
                      Defaults to ``True``.
        :param timeout: The length of time (in seconds) to wait for a response
                        before continuing if blocking is used.
                        Defaults to 
            :attr:`~sleekxmpp.xmlstream.xmlstream.XMLStream.response_timeout`.
        :param callback: Optional reference to a stream handler function. Will
                         be executed when the roster is received.
                         Implies ``block=False``.
        """
        iq = self.Iq()
        iq['type'] = 'get'
        iq.enable('roster')
        response = iq.send(block, timeout, callback)

        if callback is None:
            return self._handle_roster(response, request=True)

    def _handle_connected(self, event=None):
        #TODO: Use stream state here
        self.authenticated = False
        self.sessionstarted = False
        self.bound = False
        self.bindfail = False
        self.features = set()

    def _handle_stream_features(self, features):
        """Process the received stream features.

        :param features: The features stanza.
        """
        for order, name in self._stream_feature_order:
            if name in features['features']:
                handler, restart = self._stream_feature_handlers[name]
                if handler(features) and restart:
                    # Don't continue if the feature requires
                    # restarting the XML stream.
                    return True

    def _handle_roster(self, iq, request=False):
        """Update the roster after receiving a roster stanza.

        :param iq: The roster stanza.
        :param request: Indicates if this stanza is a response
                        to a request for the roster, and not an
                        empty acknowledgement from the server.
        """
        if iq['type'] == 'set' or (iq['type'] == 'result' and request):
            for jid in iq['roster']['items']:
                item = iq['roster']['items'][jid]
                roster = self.roster[iq['to'].bare]
                roster[jid]['name'] = item['name']
                roster[jid]['groups'] = item['groups']
                roster[jid]['from'] = item['subscription'] in ['from', 'both']
                roster[jid]['to'] = item['subscription'] in ['to', 'both']
                roster[jid]['pending_out'] = (item['ask'] == 'subscribe')
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
