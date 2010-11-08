"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from __future__ import with_statement, unicode_literals

import sys
import copy
import logging

import sleekxmpp
from sleekxmpp import plugins

from sleekxmpp.stanza import Message, Presence, Iq, Error
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

    Attributes:
       auto_authorize   -- Manage automatically accepting roster
                           subscriptions.
       auto_subscribe   -- Manage automatically requesting mutual
                           subscriptions.
       is_component     -- Indicates if this stream is for an XMPP component.
       jid              -- The XMPP JID for this stream.
       plugin           -- A dictionary of loaded plugins.
       plugin_config    -- A dictionary of plugin configurations.
       plugin_whitelist -- A list of approved plugins.
       sentpresence     -- Indicates if an initial presence has been sent.
       roster           -- A dictionary containing subscribed JIDs and
                           their presence statuses.

    Methods:
       Iq                      -- Factory for creating an Iq stanzas.
       Message                 -- Factory for creating Message stanzas.
       Presence                -- Factory for creating Presence stanzas.
       get                     -- Return a plugin given its name.
       make_iq                 -- Create and initialize an Iq stanza.
       make_iq_error           -- Create an Iq stanza of type 'error'.
       make_iq_get             -- Create an Iq stanza of type 'get'.
       make_iq_query           -- Create an Iq stanza with a given query.
       make_iq_result          -- Create an Iq stanza of type 'result'.
       make_iq_set             -- Create an Iq stanza of type 'set'.
       make_message            -- Create and initialize a Message stanza.
       make_presence           -- Create and initialize a Presence stanza.
       make_query_roster       -- Create a roster query.
       process                 -- Overrides XMLStream.process.
       register_plugin         -- Load and configure a plugin.
       register_plugins        -- Load and configure multiple plugins.
       send_message            -- Create and send a Message stanza.
       send_presence           -- Create and send a Presence stanza.
       send_presence_subscribe -- Send a subscription request.
    """

    def __init__(self, default_ns='jabber:client'):
        """
        Adapt an XML stream for use with XMPP.

        Arguments:
            default_ns -- Ensure that the correct default XML namespace
                          is used during initialization.
        """
        XMLStream.__init__(self)

        # To comply with PEP8, method names now use underscores.
        # Deprecated method names are re-mapped for backwards compatibility.
        self.registerPlugin = self.register_plugin
        self.makeIq = self.make_iq
        self.makeIqGet = self.make_iq_get
        self.makeIqResult = self.make_iq_result
        self.makeIqSet = self.make_iq_set
        self.makeIqError = self.make_iq_error
        self.makeIqQuery = self.make_iq_query
        self.makeQueryRoster = self.make_query_roster
        self.makeMessage = self.make_message
        self.makePresence = self.make_presence
        self.sendMessage = self.send_message
        self.sendPresence = self.send_presence
        self.sendPresenceSubscription = self.send_presence_subscription

        self.default_ns = default_ns
        self.stream_ns = 'http://etherx.jabber.org/streams'

        self.boundjid = JID("")

        self.plugin = {}
        self.roster = {}
        self.is_component = False
        self.auto_authorize = True
        self.auto_subscribe = True

        self.sentpresence = False

        self.register_handler(
            Callback('IM',
                     MatchXPath('{%s}message/{%s}body' % (self.default_ns,
                                                          self.default_ns)),
                     self._handle_message))
        self.register_handler(
            Callback('Presence',
                     MatchXPath("{%s}presence" % self.default_ns),
                     self._handle_presence))

        self.add_event_handler('presence_subscribe',
                               self._handle_subscribe)
        self.add_event_handler('disconnected',
                               self._handle_disconnected)

        # Set up the XML stream with XMPP's root stanzas.
        self.registerStanza(Message)
        self.registerStanza(Iq)
        self.registerStanza(Presence)

        # Initialize a few default stanza plugins.
        register_stanza_plugin(Iq, Roster)
        register_stanza_plugin(Message, Nick)
        register_stanza_plugin(Message, HTMLIM)

    def process(self, *args, **kwargs):
        """
        Ensure that plugin inter-dependencies are handled before starting
        event processing.

        Overrides XMLStream.process.
        """
        for name in self.plugin:
            if not self.plugin[name].post_inited:
                self.plugin[name].post_init()
        return XMLStream.process(self, *args, **kwargs)

    def register_plugin(self, plugin, pconfig={}, module=None):
        """
        Register and configure  a plugin for use in this stream.

        Arguments:
            plugin  -- The name of the plugin class. Plugin names must
                       be unique.
            pconfig -- A dictionary of configuration data for the plugin.
                       Defaults to an empty dictionary.
            module  -- Optional refence to the module containing the plugin
                       class if using custom plugins.
        """
        try:
            # Import the given module that contains the plugin.
            if not module:
                module = sleekxmpp.plugins
                module = __import__("%s.%s" % (module.__name__, plugin),
                                    globals(), locals(), [plugin])
            if isinstance(module, str):
                # We probably want to load a module from outside
                # the sleekxmpp package, so leave out the globals().
                module = __import__(module, fromlist=[plugin])

            # Load the plugin class from the module.
            self.plugin[plugin] = getattr(module, plugin)(self, pconfig)

            # Let XEP implementing plugins have some extra logging info.
            xep = ''
            if hasattr(self.plugin[plugin], 'xep'):
                xep = "(XEP-%s) " % self.plugin[plugin].xep

            desc = (xep, self.plugin[plugin].description)
            log.debug("Loaded Plugin %s%s" % desc)
        except:
            log.exception("Unable to load plugin: %s", plugin)

    def register_plugins(self):
        """
        Register and initialize all built-in plugins.

        Optionally, the list of plugins loaded may be limited to those
        contained in self.plugin_whitelist.

        Plugin configurations stored in self.plugin_config will be used.
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
        """
        Return a plugin given its name, if it has been registered.
        """
        if key in self.plugin:
            return self.plugin[key]
        else:
            log.warning("""Plugin "%s" is not loaded.""" % key)
            return False

    def get(self, key, default):
        """
        Return a plugin given its name, if it has been registered.
        """
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

    def make_iq(self, id=0, ifrom=None):
        """
        Create a new Iq stanza with a given Id and from JID.

        Arguments:
            id    -- An ideally unique ID value for this stanza thread.
                     Defaults to 0.
            ifrom -- The from JID to use for this stanza.
        """
        return self.Iq()._set_stanza_values({'id': str(id),
                                             'from': ifrom})

    def make_iq_get(self, queryxmlns=None):
        """
        Create an Iq stanza of type 'get'.

        Optionally, a query element may be added.

        Arguments:
            queryxmlns -- The namespace of the query to use.
        """
        return self.Iq()._set_stanza_values({'type': 'get',
                                             'query': queryxmlns})

    def make_iq_result(self, id):
        """
        Create an Iq stanza of type 'result' with the given ID value.

        Arguments:
            id -- An ideally unique ID value. May use self.new_id().
        """
        return self.Iq()._set_stanza_values({'id': id,
                                             'type': 'result'})

    def make_iq_set(self, sub=None):
        """
        Create an Iq stanza of type 'set'.

        Optionally, a substanza may be given to use as the
        stanza's payload.

        Arguments:
            sub -- A stanza or XML object to use as the Iq's payload.
        """
        iq = self.Iq()._set_stanza_values({'type': 'set'})
        if sub != None:
            iq.append(sub)
        return iq

    def make_iq_error(self, id, type='cancel',
                      condition='feature-not-implemented', text=None):
        """
        Create an Iq stanza of type 'error'.

        Arguments:
            id        -- An ideally unique ID value. May use self.new_id().
            type      -- The type of the error, such as 'cancel' or 'modify'.
                         Defaults to 'cancel'.
            condition -- The error condition.
                         Defaults to 'feature-not-implemented'.
            text      -- A message describing the cause of the error.
        """
        iq = self.Iq()._set_stanza_values({'id': id})
        iq['error']._set_stanza_values({'type': type,
                                        'condition': condition,
                                        'text': text})
        return iq

    def make_iq_query(self, iq=None, xmlns=''):
        """
        Create or modify an Iq stanza to use the given
        query namespace.

        Arguments:
            iq    -- Optional Iq stanza to modify. A new
                     stanza is created otherwise.
            xmlns -- The query's namespace.
        """
        if not iq:
            iq = self.Iq()
        iq['query'] = xmlns
        return iq

    def make_query_roster(self, iq=None):
        """
        Create a roster query element.

        Arguments:
            iq -- Optional Iq stanza to modify. A new stanza
                  is created otherwise.
        """
        if iq:
            iq['query'] = 'jabber:iq:roster'
        return ET.Element("{jabber:iq:roster}query")

    def make_message(self, mto, mbody=None, msubject=None, mtype=None,
                     mhtml=None, mfrom=None, mnick=None):
        """
        Create and initialize a new Message stanza.

        Arguments:
            mto      -- The recipient of the message.
            mbody    -- The main contents of the message.
            msubject -- Optional subject for the message.
            mtype    -- The message's type, such as 'chat' or 'groupchat'.
            mhtml    -- Optional HTML body content.
            mfrom    -- The sender of the message. If sending from a client,
                        be aware that some servers require that the full JID
                        of the sender be used.
            mnick    -- Optional nickname of the sender.
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
                      pto=None, ptype=None, pfrom=None):
        """
        Create and initialize a new Presence stanza.

        Arguments:
            pshow     -- The presence's show value.
            pstatus   -- The presence's status message.
            ppriority -- This connections' priority.
            pto       -- The recipient of a directed presence.
            ptype     -- The type of presence, such as 'subscribe'.
            pfrom     -- The sender of the presence.
        """
        presence = self.Presence(stype=ptype, sfrom=pfrom, sto=pto)
        if pshow is not None:
            presence['type'] = pshow
        if pfrom is None:
            presence['from'] = self.boundjid.full
        presence['priority'] = ppriority
        presence['status'] = pstatus
        return presence

    def send_message(self, mto, mbody, msubject=None, mtype=None,
                     mhtml=None, mfrom=None, mnick=None):
        """
        Create, initialize, and send a Message stanza.


        """
        self.makeMessage(mto, mbody, msubject, mtype,
                         mhtml, mfrom, mnick).send()

    def send_presence(self, pshow=None, pstatus=None, ppriority=None,
                      pto=None, pfrom=None, ptype=None):
        """
        Create, initialize, and send a Presence stanza.

        Arguments:
            pshow     -- The presence's show value.
            pstatus   -- The presence's status message.
            ppriority -- This connections' priority.
            pto       -- The recipient of a directed presence.
            ptype     -- The type of presence, such as 'subscribe'.
            pfrom     -- The sender of the presence.
        """
        self.makePresence(pshow, pstatus, ppriority, pto,
                          ptype=ptype, pfrom=pfrom).send()
        # Unexpected errors may occur if
        if not self.sentpresence:
            self.event('sent_presence')
            self.sentpresence = True

    def send_presence_subscription(self, pto, pfrom=None,
                                   ptype='subscribe', pnick=None):
        """
        Create, initialize, and send a Presence stanza of type 'subscribe'.

        Arguments:
            pto   -- The recipient of a directed presence.
            pfrom -- The sender of the presence.
            ptype -- The type of presence. Defaults to 'subscribe'.
            pnick -- Nickname of the presence's sender.
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
        """
        Attribute accessor for bare jid
        """
        log.warning("jid property deprecated. Use boundjid.bare")
        return self.boundjid.bare

    @jid.setter
    def jid(self, value):
        log.warning("jid property deprecated. Use boundjid.bare")
        self.boundjid.bare = value

    @property
    def fulljid(self):
        """
        Attribute accessor for full jid
        """
        log.warning("fulljid property deprecated. Use boundjid.full")
        return self.boundjid.full

    @fulljid.setter
    def fulljid(self, value):
        log.warning("fulljid property deprecated. Use boundjid.full")
        self.boundjid.full = value

    @property
    def resource(self):
        """
        Attribute accessor for jid resource
        """
        log.warning("resource property deprecated. Use boundjid.resource")
        return self.boundjid.resource

    @resource.setter
    def resource(self, value):
        log.warning("fulljid property deprecated. Use boundjid.full")
        self.boundjid.resource = value

    @property
    def username(self):
        """
        Attribute accessor for jid usernode
        """
        log.warning("username property deprecated. Use boundjid.user")
        return self.boundjid.user

    @username.setter
    def username(self, value):
        log.warning("username property deprecated. Use boundjid.user")
        self.boundjid.user = value

    @property
    def server(self):
        """
        Attribute accessor for jid host
        """
        log.warning("server property deprecated. Use boundjid.host")
        return self.boundjid.server

    @server.setter
    def server(self, value):
        log.warning("server property deprecated. Use boundjid.host")
        self.boundjid.server = value

    def set_jid(self, jid):
        """Rip a JID apart and claim it as our own."""
        log.debug("setting jid to %s" % jid)
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
        self.roster = {}

    def _handle_message(self, msg):
        """Process incoming message stanzas."""
        self.event('message', msg)

    def _handle_presence(self, presence):
        """
        Process incoming presence stanzas.

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

        # Strip the information from the stanza.
        jid = presence['from'].bare
        resource = presence['from'].resource
        show = presence['type']
        status = presence['status']
        priority = presence['priority']

        was_offline = False
        got_online = False
        old_roster = self.roster.get(jid, {}).get(resource, {})

        # Create a new roster entry if needed.
        if not jid in self.roster:
            self.roster[jid] = {'groups': [],
                                'name': '',
                                'subscription': 'none',
                                'presence': {},
                                'in_roster': False}

        # Alias to simplify some references.
        connections = self.roster[jid]['presence']

        # Determine if the user has just come online.
        if not resource in connections:
            if show == 'available' or show in presence.showtypes:
                got_online = True
            was_offline = True
            connections[resource] = {}

        if connections[resource].get('show', 'unavailable') == 'unavailable':
            was_offline = True

        # Update the roster's state for this JID's resource.
        connections[resource] = {'show': show,
                                'status': status,
                                'priority': priority}

        name = self.roster[jid].get('name', '')

        # Remove unneeded state information after a resource
        # disconnects. Determine if this was the last connection
        # for the JID.
        if show == 'unavailable':
            log.debug("%s %s got offline" % (jid, resource))
            del connections[resource]

            if not connections and not self.roster[jid]['in_roster']:
                del self.roster[jid]
            if not was_offline:
                self.event("got_offline", presence)
            else:
                return False

        name = '(%s) ' % name if name else ''

        # Presence state has changed.
        self.event("changed_status", presence)
        if got_online:
            self.event("got_online", presence)
        log.debug("STATUS: %s%s/%s[%s]: %s" % (name, jid, resource,
                                                   show, status))

    def _handle_subscribe(self, presence):
        """
        Automatically managage subscription requests.

        Subscription behavior is controlled by the settings
        self.auto_authorize and self.auto_subscribe.

        auto_auth  auto_sub   Result:
        True       True       Create bi-directional subsriptions.
        True       False      Create only directed subscriptions.
        False      *          Decline all subscriptions.
        None       *          Disable automatic handling and use
                              a custom handler.
        """
        presence.reply()
        presence['to'] = presence['to'].bare

        # We are using trinary logic, so conditions have to be
        # more explicit than usual.
        if self.auto_authorize == True:
            presence['type'] = 'subscribed'
            presence.send()
            if self.auto_subscribe:
                presence['type'] = 'subscribe'
                presence.send()
        elif self.auto_authorize == False:
            presence['type'] = 'unsubscribed'
            presence.send()

# Restore the old, lowercased name for backwards compatibility.
basexmpp = BaseXMPP
