# -*- coding: utf-8 -*-
"""
    sleekxmpp.basexmpp
    ~~~~~~~~~~~~~~~~~~

    This module provides the common XMPP functionality
    for both clients and components.

    Part of SleekXMPP: The Sleek XMPP Library

    :copyright: (c) 2011 Nathanael C. Fritz
    :license: MIT, see LICENSE for more details
"""

from __future__ import with_statement, unicode_literals

import sys
import copy
import logging

import sleekxmpp
from sleekxmpp import plugins, roster
from sleekxmpp.exceptions import IqError, IqTimeout

from sleekxmpp.stanza import Message, Presence, Iq, Error, StreamError
from sleekxmpp.stanza.roster import Roster
from sleekxmpp.stanza.nick import Nick
from sleekxmpp.stanza.htmlim import HTMLIM

from sleekxmpp.xmlstream import XMLStream, JID, tostring
from sleekxmpp.xmlstream import ET, register_stanza_plugin
from sleekxmpp.xmlstream.matcher import *
from sleekxmpp.xmlstream.handler import *


log = logging.getLogger(__name__)

# In order to make sure that Unicode is handled properly
# in Python 2.x, reset the default encoding.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')


class BaseXMPP(XMLStream):

    """
    The BaseXMPP class adapts the generic XMLStream class for use
    with XMPP. It also provides a plugin mechanism to easily extend
    and add support for new XMPP features.

    :param default_ns: Ensure that the correct default XML namespace
                       is used during initialization.
    """

    def __init__(self, jid='', default_ns='jabber:client'):
        XMLStream.__init__(self)

        self.default_ns = default_ns
        self.stream_ns = 'http://etherx.jabber.org/streams'
        self.namespace_map[self.stream_ns] = 'stream'

        #: An identifier for the stream as given by the server.
        self.stream_id = None

        #: The JabberID (JID) used by this connection. 
        self.boundjid = JID(jid)

        #: A dictionary mapping plugin names to plugins.
        self.plugin = {}

        #: Configuration options for whitelisted plugins.
        #: If a plugin is registered without any configuration,
        #: and there is an entry here, it will be used.
        self.plugin_config = {}

        #: A list of plugins that will be loaded if
        #: :meth:`register_plugins` is called.
        self.plugin_whitelist = []

        #: The main roster object. This roster supports multiple
        #: owner JIDs, as in the case for components. For clients
        #: which only have a single JID, see :attr:`client_roster`.
        self.roster = roster.Roster(self)
        self.roster.add(self.boundjid.bare)

        #: The single roster for the bound JID. This is the
        #: equivalent of::
        #:
        #:     self.roster[self.boundjid.bare]
        self.client_roster = self.roster[self.boundjid.bare]

        #: The distinction between clients and components can be
        #: important, primarily for choosing how to handle the
        #: ``'to'`` and ``'from'`` JIDs of stanzas.
        self.is_component = False

        #: Flag indicating that the initial presence broadcast has
        #: been sent. Until this happens, some servers may not
        #: behave as expected when sending stanzas.
        self.sentpresence = False

        #: A reference to :mod:`sleekxmpp.stanza` to make accessing
        #: stanza classes easier.
        self.stanza = sleekxmpp.stanza

        self.register_handler(
            Callback('IM',
                     MatchXPath('{%s}message/{%s}body' % (self.default_ns,
                                                          self.default_ns)),
                     self._handle_message))
        self.register_handler(
            Callback('Presence',
                     MatchXPath("{%s}presence" % self.default_ns),
                     self._handle_presence))
        self.register_handler(
            Callback('Stream Error',
                     MatchXPath("{%s}error" % self.stream_ns),
                     self._handle_stream_error))

        self.add_event_handler('disconnected',
                               self._handle_disconnected)
        self.add_event_handler('presence_available',
                               self._handle_available)
        self.add_event_handler('presence_dnd',
                               self._handle_available)
        self.add_event_handler('presence_xa',
                               self._handle_available)
        self.add_event_handler('presence_chat',
                               self._handle_available)
        self.add_event_handler('presence_away',
                               self._handle_available)
        self.add_event_handler('presence_unavailable',
                               self._handle_unavailable)
        self.add_event_handler('presence_subscribe',
                               self._handle_subscribe)
        self.add_event_handler('presence_subscribed',
                               self._handle_subscribed)
        self.add_event_handler('presence_unsubscribe',
                               self._handle_unsubscribe)
        self.add_event_handler('presence_unsubscribed',
                               self._handle_unsubscribed)
        self.add_event_handler('roster_subscription_request',
                               self._handle_new_subscription)

        # Set up the XML stream with XMPP's root stanzas.
        self.register_stanza(Message)
        self.register_stanza(Iq)
        self.register_stanza(Presence)
        self.register_stanza(StreamError)

        # Initialize a few default stanza plugins.
        register_stanza_plugin(Iq, Roster)
        register_stanza_plugin(Message, Nick)
        register_stanza_plugin(Message, HTMLIM)

    def start_stream_handler(self, xml):
        """Save the stream ID once the streams have been established.

        :param xml: The incoming stream's root element.
        """
        self.stream_id = xml.get('id', '')

    def process(self, *args, **kwargs):
        """Initialize plugins and begin processing the XML stream.

        The number of threads used for processing stream events is determined
        by :data:`HANDLER_THREADS`.

        :param bool block: If ``False``, then event dispatcher will run
                    in a separate thread, allowing for the stream to be
                    used in the background for another application.
                    Otherwise, ``process(block=True)`` blocks the current
                    thread. Defaults to ``False``.
        :param bool threaded: **DEPRECATED**
                    If ``True``, then event dispatcher will run
                    in a separate thread, allowing for the stream to be
                    used in the background for another application.
                    Defaults to ``True``. This does **not** mean that no
                    threads are used at all if ``threaded=False``.

        Regardless of these threading options, these threads will 
        always exist:

        - The event queue processor
        - The send queue processor
        - The scheduler
        """
        for name in self.plugin:
            if not self.plugin[name].post_inited:
                self.plugin[name].post_init()
        return XMLStream.process(self, *args, **kwargs)

    def register_plugin(self, plugin, pconfig={}, module=None):
        """Register and configure  a plugin for use in this stream.

        :param plugin: The name of the plugin class. Plugin names must
                       be unique.
        :param pconfig: A dictionary of configuration data for the plugin.
                        Defaults to an empty dictionary.
        :param module: Optional refence to the module containing the plugin
                       class if using custom plugins.
        """
        try:
            # Import the given module that contains the plugin.
            if not module:
                try:
                    module = sleekxmpp.plugins
                    module = __import__(
                            str("%s.%s" % (module.__name__, plugin)),
                            globals(), locals(), [str(plugin)])
                except ImportError:
                    module = sleekxmpp.features
                    module = __import__(
                            str("%s.%s" % (module.__name__, plugin)),
                            globals(), locals(), [str(plugin)])
            if isinstance(module, str):
                # We probably want to load a module from outside
                # the sleekxmpp package, so leave out the globals().
                module = __import__(module, fromlist=[plugin])

            # Use the global plugin config cache, if applicable
            if not pconfig:
                pconfig = self.plugin_config.get(plugin, {})

            # Load the plugin class from the module.
            self.plugin[plugin] = getattr(module, plugin)(self, pconfig)

            # Let XEP/RFC implementing plugins have some extra logging info.
            spec = '(CUSTOM) %s'
            if self.plugin[plugin].xep:
                spec = "(XEP-%s) " % self.plugin[plugin].xep
            elif self.plugin[plugin].rfc:
                spec = "(RFC-%s) " % self.plugin[plugin].rfc

            desc = (spec, self.plugin[plugin].description)
            log.debug("Loaded Plugin %s %s" % desc)
        except:
            log.exception("Unable to load plugin: %s", plugin)

    def register_plugins(self):
        """Register and initialize all built-in plugins.

        Optionally, the list of plugins loaded may be limited to those
        contained in :attr:`plugin_whitelist`.

        Plugin configurations stored in :attr:`plugin_config` will be used.
        """
        if self.plugin_whitelist:
            plugin_list = self.plugin_whitelist
        else:
            plugin_list = plugins.__all__

        for plugin in plugin_list:
            if plugin in plugins.__all__:
                self.register_plugin(plugin,
                                     self.plugin_config.get(plugin, {}))
            else:
                raise NameError("Plugin %s not in plugins.__all__." % plugin)

        # Resolve plugin inter-dependencies.
        for plugin in self.plugin:
            self.plugin[plugin].post_init()

    def __getitem__(self, key):
        """Return a plugin given its name, if it has been registered."""
        if key in self.plugin:
            return self.plugin[key]
        else:
            log.warning("Plugin '%s' is not loaded.", key)
            return False

    def get(self, key, default):
        """Return a plugin given its name, if it has been registered."""
        return self.plugin.get(key, default)

    def Message(self, *args, **kwargs):
        """Create a Message stanza associated with this stream."""
        return Message(self, *args, **kwargs)

    def Iq(self, *args, **kwargs):
        """Create an Iq stanza associated with this stream."""
        return Iq(self, *args, **kwargs)

    def Presence(self, *args, **kwargs):
        """Create a Presence stanza associated with this stream."""
        return Presence(self, *args, **kwargs)

    def make_iq(self, id=0, ifrom=None, ito=None, itype=None, iquery=None):
        """Create a new Iq stanza with a given Id and from JID.

        :param id: An ideally unique ID value for this stanza thread.
                   Defaults to 0.
        :param ifrom: The from :class:`~sleekxmpp.xmlstream.jid.JID` 
                      to use for this stanza.
        :param ito: The destination :class:`~sleekxmpp.xmlstream.jid.JID`
                    for this stanza.
        :param itype: The :class:`~sleekxmpp.stanza.iq.Iq`'s type, 
                      one of: ``'get'``, ``'set'``, ``'result'``,
                      or ``'error'``.
        :param iquery: Optional namespace for adding a query element.
        """
        iq = self.Iq()
        iq['id'] = str(id)
        iq['to'] = ito
        iq['from'] = ifrom
        iq['type'] = itype
        iq['query'] = iquery
        return iq

    def make_iq_get(self, queryxmlns=None, ito=None, ifrom=None, iq=None):
        """Create an :class:`~sleekxmpp.stanza.iq.Iq` stanza of type ``'get'``.

        Optionally, a query element may be added.

        :param queryxmlns: The namespace of the query to use.
        :param ito: The destination :class:`~sleekxmpp.xmlstream.jid.JID`
                    for this stanza.
        :param ifrom: The ``'from'`` :class:`~sleekxmpp.xmlstream.jid.JID`
                      to use for this stanza.
        :param iq: Optionally use an existing stanza instead
                   of generating a new one.
        """
        if not iq:
            iq = self.Iq()
        iq['type'] = 'get'
        iq['query'] = queryxmlns
        if ito:
            iq['to'] = ito
        if ifrom:
            iq['from'] = ifrom
        return iq

    def make_iq_result(self, id=None, ito=None, ifrom=None, iq=None):
        """
        Create an :class:`~sleekxmpp.stanza.iq.Iq` stanza of type 
        ``'result'`` with the given ID value.

        :param id: An ideally unique ID value. May use :meth:`new_id()`.
        :param ito: The destination :class:`~sleekxmpp.xmlstream.jid.JID`
                    for this stanza.
        :param ifrom: The ``'from'`` :class:`~sleekxmpp.xmlstream.jid.JID`
                      to use for this stanza.
        :param iq: Optionally use an existing stanza instead
                   of generating a new one.
        """
        if not iq:
            iq = self.Iq()
            if id is None:
                id = self.new_id()
            iq['id'] = id
        iq['type'] = 'result'
        if ito:
            iq['to'] = ito
        if ifrom:
            iq['from'] = ifrom
        return iq

    def make_iq_set(self, sub=None, ito=None, ifrom=None, iq=None):
        """
        Create an :class:`~sleekxmpp.stanza.iq.Iq` stanza of type ``'set'``.

        Optionally, a substanza may be given to use as the
        stanza's payload.

        :param sub: Either an 
                    :class:`~sleekxmpp.xmlstream.stanzabase.ElementBase`
                    stanza object or an
                    :class:`~xml.etree.ElementTree.Element` XML object 
                    to use as the :class:`~sleekxmpp.stanza.iq.Iq`'s payload.
        :param ito: The destination :class:`~sleekxmpp.xmlstream.jid.JID`
                    for this stanza.
        :param ifrom: The ``'from'`` :class:`~sleekxmpp.xmlstream.jid.JID`
                      to use for this stanza.
        :param iq: Optionally use an existing stanza instead
                   of generating a new one.
        """
        if not iq:
            iq = self.Iq()
        iq['type'] = 'set'
        if sub != None:
            iq.append(sub)
        if ito:
            iq['to'] = ito
        if ifrom:
            iq['from'] = ifrom
        return iq

    def make_iq_error(self, id, type='cancel',
                      condition='feature-not-implemented',
                      text=None, ito=None, ifrom=None, iq=None):
        """
        Create an :class:`~sleekxmpp.stanza.iq.Iq` stanza of type ``'error'``.

        :param id: An ideally unique ID value. May use :meth:`new_id()`.
        :param type: The type of the error, such as ``'cancel'`` or 
                     ``'modify'``. Defaults to ``'cancel'``.
        :param condition: The error condition. Defaults to 
                          ``'feature-not-implemented'``.
        :param text: A message describing the cause of the error.
        :param ito: The destination :class:`~sleekxmpp.xmlstream.jid.JID`
                    for this stanza.
        :param ifrom: The ``'from'`` :class:`~sleekxmpp.xmlstream.jid.JID`
                      to use for this stanza.
        :param iq: Optionally use an existing stanza instead
                   of generating a new one.
        """
        if not iq:
            iq = self.Iq()
        iq['id'] = id
        iq['error']['type'] = type
        iq['error']['condition'] = condition
        iq['error']['text'] = text
        if ito:
            iq['to'] = ito
        if ifrom:
            iq['from'] = ifrom
        return iq

    def make_iq_query(self, iq=None, xmlns='', ito=None, ifrom=None):
        """
        Create or modify an :class:`~sleekxmpp.stanza.iq.Iq` stanza 
        to use the given query namespace.

        :param iq: Optionally use an existing stanza instead
                   of generating a new one.
        :param xmlns: The query's namespace.
        :param ito: The destination :class:`~sleekxmpp.xmlstream.jid.JID`
                    for this stanza.
        :param ifrom: The ``'from'`` :class:`~sleekxmpp.xmlstream.jid.JID`
                      to use for this stanza.
        """
        if not iq:
            iq = self.Iq()
        iq['query'] = xmlns
        if ito:
            iq['to'] = ito
        if ifrom:
            iq['from'] = ifrom
        return iq

    def make_query_roster(self, iq=None):
        """Create a roster query element.

        :param iq: Optionally use an existing stanza instead
                   of generating a new one.
        """
        if iq:
            iq['query'] = 'jabber:iq:roster'
        return ET.Element("{jabber:iq:roster}query")

    def make_message(self, mto, mbody=None, msubject=None, mtype=None,
                     mhtml=None, mfrom=None, mnick=None):
        """
        Create and initialize a new 
        :class:`~sleekxmpp.stanza.message.Message` stanza.

        :param mto: The recipient of the message.
        :param mbody: The main contents of the message.
        :param msubject: Optional subject for the message.
        :param mtype: The message's type, such as ``'chat'`` or
                      ``'groupchat'``.
        :param mhtml: Optional HTML body content in the form of a string.
        :param mfrom: The sender of the message. if sending from a client,
                      be aware that some servers require that the full JID
                      of the sender be used.
        :param mnick: Optional nickname of the sender.
        """
        message = self.Message(sto=mto, stype=mtype, sfrom=mfrom)
        message['body'] = mbody
        message['subject'] = msubject
        if mnick is not None:
            message['nick'] = mnick
        if mhtml is not None:
            message['html']['body'] = mhtml
        return message

    def make_presence(self, pshow=None, pstatus=None, ppriority=None,
                      pto=None, ptype=None, pfrom=None, pnick=None):
        """
        Create and initialize a new 
        :class:`~sleekxmpp.stanza.presence.Presence` stanza.

        :param pshow: The presence's show value.
        :param pstatus: The presence's status message.
        :param ppriority: This connection's priority.
        :param pto: The recipient of a directed presence.
        :param ptype: The type of presence, such as ``'subscribe'``.
        :param pfrom: The sender of the presence.
        :param pnick: Optional nickname of the presence's sender.
        """
        presence = self.Presence(stype=ptype, sfrom=pfrom, sto=pto)
        if pshow is not None:
            presence['type'] = pshow
        if pfrom is None and self.is_component:
            presence['from'] = self.boundjid.full
        presence['priority'] = ppriority
        presence['status'] = pstatus
        presence['nick'] = pnick
        return presence

    def send_message(self, mto, mbody, msubject=None, mtype=None,
                     mhtml=None, mfrom=None, mnick=None):
        """
        Create, initialize, and send a new 
        :class:`~sleekxmpp.stanza.message.Message` stanza.

        :param mto: The recipient of the message.
        :param mbody: The main contents of the message.
        :param msubject: Optional subject for the message.
        :param mtype: The message's type, such as ``'chat'`` or
                      ``'groupchat'``.
        :param mhtml: Optional HTML body content in the form of a string.
        :param mfrom: The sender of the message. if sending from a client,
                      be aware that some servers require that the full JID
                      of the sender be used.
        :param mnick: Optional nickname of the sender.
        """
        self.make_message(mto, mbody, msubject, mtype,
                          mhtml, mfrom, mnick).send()

    def send_presence(self, pshow=None, pstatus=None, ppriority=None,
                      pto=None, pfrom=None, ptype=None, pnick=None):
        """
        Create, initialize, and send a new 
        :class:`~sleekxmpp.stanza.presence.Presence` stanza.

        :param pshow: The presence's show value.
        :param pstatus: The presence's status message.
        :param ppriority: This connection's priority.
        :param pto: The recipient of a directed presence.
        :param ptype: The type of presence, such as ``'subscribe'``.
        :param pfrom: The sender of the presence.
        :param pnick: Optional nickname of the presence's sender.
        """
        # Python2.6 chokes on Unicode strings for dict keys.
        args = {str('pto'): pto,
                str('ptype'): ptype,
                str('pshow'): pshow,
                str('pstatus'): pstatus,
                str('ppriority'): ppriority,
                str('pnick'): pnick}

        if self.is_component:
            self.roster[pfrom].send_presence(**args)
        else:
            self.client_roster.send_presence(**args)

    def send_presence_subscription(self, pto, pfrom=None,
                                   ptype='subscribe', pnick=None):
        """
        Create, initialize, and send a new 
        :class:`~sleekxmpp.stanza.presence.Presence` stanza of
        type ``'subscribe'``.

        :param pto: The recipient of a directed presence.
        :param pfrom: The sender of the presence.
        :param ptype: The type of presence, such as ``'subscribe'``.
        :param pnick: Optional nickname of the presence's sender.
        """
        presence = self.makePresence(ptype=ptype,
                                     pfrom=pfrom,
                                     pto=self.getjidbare(pto))
        if pnick:
            nick = ET.Element('{http://jabber.org/protocol/nick}nick')
            nick.text = pnick
            presence.append(nick)
        presence.send()

    @property
    def jid(self):
        """Attribute accessor for bare jid"""
        log.warning("jid property deprecated. Use boundjid.bare")
        return self.boundjid.bare

    @jid.setter
    def jid(self, value):
        log.warning("jid property deprecated. Use boundjid.bare")
        self.boundjid.bare = value

    @property
    def fulljid(self):
        """Attribute accessor for full jid"""
        log.warning("fulljid property deprecated. Use boundjid.full")
        return self.boundjid.full

    @fulljid.setter
    def fulljid(self, value):
        log.warning("fulljid property deprecated. Use boundjid.full")
        self.boundjid.full = value

    @property
    def resource(self):
        """Attribute accessor for jid resource"""
        log.warning("resource property deprecated. Use boundjid.resource")
        return self.boundjid.resource

    @resource.setter
    def resource(self, value):
        log.warning("fulljid property deprecated. Use boundjid.full")
        self.boundjid.resource = value

    @property
    def username(self):
        """Attribute accessor for jid usernode"""
        log.warning("username property deprecated. Use boundjid.user")
        return self.boundjid.user

    @username.setter
    def username(self, value):
        log.warning("username property deprecated. Use boundjid.user")
        self.boundjid.user = value

    @property
    def server(self):
        """Attribute accessor for jid host"""
        log.warning("server property deprecated. Use boundjid.host")
        return self.boundjid.server

    @server.setter
    def server(self, value):
        log.warning("server property deprecated. Use boundjid.host")
        self.boundjid.server = value

    @property
    def auto_authorize(self):
        """Auto accept or deny subscription requests.

        If ``True``, auto accept subscription requests.
        If ``False``, auto deny subscription requests.
        If ``None``, don't automatically respond.
        """
        return self.roster.auto_authorize

    @auto_authorize.setter
    def auto_authorize(self, value):
        self.roster.auto_authorize = value

    @property
    def auto_subscribe(self):
        """Auto send requests for mutual subscriptions.

        If ``True``, auto send mutual subscription requests.
        """
        return self.roster.auto_subscribe

    @auto_subscribe.setter
    def auto_subscribe(self, value):
        self.roster.auto_subscribe = value

    def set_jid(self, jid):
        """Rip a JID apart and claim it as our own."""
        log.debug("setting jid to %s", jid)
        self.boundjid.full = jid

    def getjidresource(self, fulljid):
        if '/' in fulljid:
            return fulljid.split('/', 1)[-1]
        else:
            return ''

    def getjidbare(self, fulljid):
        return fulljid.split('/', 1)[0]

    def _handle_disconnected(self, event):
        """When disconnected, reset the roster"""
        self.roster.reset()

    def _handle_stream_error(self, error):
        self.event('stream_error', error)

    def _handle_message(self, msg):
        """Process incoming message stanzas."""
        self.event('message', msg)

    def _handle_available(self, presence):
        pto = presence['to'].bare
        pfrom = presence['from'].bare
        self.roster[pto][pfrom].handle_available(presence)

    def _handle_unavailable(self, presence):
        pto = presence['to'].bare
        pfrom = presence['from'].bare
        self.roster[pto][pfrom].handle_unavailable(presence)

    def _handle_new_subscription(self, stanza):
        """Attempt to automatically handle subscription requests.

        Subscriptions will be approved if the request is from
        a whitelisted JID, of :attr:`auto_authorize` is True. They
        will be rejected if :attr:`auto_authorize` is False. Setting
        :attr:`auto_authorize` to ``None`` will disable automatic
        subscription handling (except for whitelisted JIDs).

        If a subscription is accepted, a request for a mutual
        subscription will be sent if :attr:`auto_subscribe` is ``True``.
        """
        roster = self.roster[stanza['to'].bare]
        item = self.roster[stanza['to'].bare][stanza['from'].bare]
        if item['whitelisted']:
            item.authorize()
        elif roster.auto_authorize:
            item.authorize()
            if roster.auto_subscribe:
                item.subscribe()
        elif roster.auto_authorize == False:
            item.unauthorize()

    def _handle_removed_subscription(self, presence):
        pto = presence['to'].bare
        pfrom = presence['from'].bare
        self.roster[pto][pfrom].unauthorize()

    def _handle_subscribe(self, presence):
        pto = presence['to'].bare
        pfrom = presence['from'].bare
        self.roster[pto][pfrom].handle_subscribe(presence)

    def _handle_subscribed(self, presence):
        pto = presence['to'].bare
        pfrom = presence['from'].bare
        self.roster[pto][pfrom].handle_subscribed(presence)

    def _handle_unsubscribe(self, presence):
        pto = presence['to'].bare
        pfrom = presence['from'].bare
        self.roster[pto][pfrom].handle_unsubscribe(presence)

    def _handle_unsubscribed(self, presence):
        pto = presence['to'].bare
        pfrom = presence['from'].bare
        self.roster[pto][pfrom].handle_unsubscribed(presence)

    def _handle_presence(self, presence):
        """Process incoming presence stanzas.

        Update the roster with presence information.
        """
        self.event("presence_%s" % presence['type'], presence)

        # Check for changes in subscription state.
        if presence['type'] in ('subscribe', 'subscribed',
                                'unsubscribe', 'unsubscribed'):
            self.event('changed_subscription', presence)
            return
        elif not presence['type'] in ('available', 'unavailable') and \
             not presence['type'] in presence.showtypes:
            return

    def exception(self, exception):
        """Process any uncaught exceptions, notably 
        :class:`~sleekxmpp.exceptions.IqError` and
        :class:`~sleekxmpp.exceptions.IqTimeout` exceptions.

        :param exception: An unhandled :class:`Exception` object.
        """
        if isinstance(exception, IqError):
            iq = exception.iq
            log.error('%s: %s', iq['error']['condition'],
                                iq['error']['text'])
            log.warning('You should catch IqError exceptions')
        elif isinstance(exception, IqTimeout):
            iq = exception.iq
            log.error('Request timed out: %s', iq)
            log.warning('You should catch IqTimeout exceptions')
        else:
            log.exception(exception)


# Restore the old, lowercased name for backwards compatibility.
basexmpp = BaseXMPP

# To comply with PEP8, method names now use underscores.
# Deprecated method names are re-mapped for backwards compatibility.
BaseXMPP.registerPlugin = BaseXMPP.register_plugin
BaseXMPP.makeIq = BaseXMPP.make_iq
BaseXMPP.makeIqGet = BaseXMPP.make_iq_get
BaseXMPP.makeIqResult = BaseXMPP.make_iq_result
BaseXMPP.makeIqSet = BaseXMPP.make_iq_set
BaseXMPP.makeIqError = BaseXMPP.make_iq_error
BaseXMPP.makeIqQuery = BaseXMPP.make_iq_query
BaseXMPP.makeQueryRoster = BaseXMPP.make_query_roster
BaseXMPP.makeMessage = BaseXMPP.make_message
BaseXMPP.makePresence = BaseXMPP.make_presence
BaseXMPP.sendMessage = BaseXMPP.send_message
BaseXMPP.sendPresence = BaseXMPP.send_presence
BaseXMPP.sendPresenceSubscription = BaseXMPP.send_presence_subscription
