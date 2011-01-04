"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

import sleekxmpp
from sleekxmpp import Iq
from sleekxmpp.exceptions import XMPPError
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.xmlstream import register_stanza_plugin, ElementBase, ET, JID
from sleekxmpp.plugins.xep_0030 import DiscoInfo, DiscoItems, StaticDisco


log = logging.getLogger(__name__)


class xep_0030(base_plugin):

    """
    XEP-0030: Service Discovery

    Service discovery in XMPP allows entities to discover information about
    other agents in the network, such as the feature sets supported by a
    client, or signposts to other, related entities.

    Also see <http://www.xmpp.org/extensions/xep-0030.html>.

    The XEP-0030 plugin works using a hierarchy of dynamic
    node handlers, ranging from global handlers to specific
    JID+node handlers. The default set of handlers operate
    in a static manner, storing disco information in memory.
    However, custom handlers may use any available backend
    storage mechanism desired, such as SQLite or Redis.

    Node handler hierarchy:
        JID   | Node  | Level
        ---------------------
        None  | None  | Global
        Given | None  | All nodes for the JID
        None  | Given | Node on self.xmpp.boundjid
        Given | Given | A single node

    Stream Handlers:
        Disco Info  -- Any Iq stanze that includes a query with the
                       namespace http://jabber.org/protocol/disco#info.
        Disco Items -- Any Iq stanze that includes a query with the
                       namespace http://jabber.org/protocol/disco#items.

    Events:
        disco_info         -- Received a disco#info Iq query result.
        disco_items        -- Received a disco#items Iq query result.
        disco_info_query   -- Received a disco#info Iq query request.
        disco_items_query  -- Received a disco#items Iq query request.

    Attributes:
        stanza -- A reference to the module containing the stanza classes
                  provided by this plugin.
        static -- Object containing the default set of static node handlers.
        xmpp   -- The main SleekXMPP object.

    Methods:
        set_node_handler -- Assign a handler to a JID/node combination.
        del_node_handler -- Remove a handler from a JID/node combination.
        get_info         -- Retrieve disco#info data, locally or remote.
        get_items        -- Retrieve disco#items data, locally or remote.
        set_identities   --
        set_features     --
        set_items        --
        del_items        --
        del_identity     --
        del_feature      --
        del_item         --
        add_identity     --
        add_feature      --
        add_item         --
    """

    def plugin_init(self):
        """
        Start the XEP-0030 plugin.
        """
        self.xep = '0030'
        self.description = 'Service Discovery'
        self.stanza = sleekxmpp.plugins.xep_0030.stanza

        # Retain some backwards compatibility
        self.getInfo = self.get_info
        self.getItems = self.get_items

        self.xmpp.register_handler(
                Callback('Disco Info',
                         StanzaPath('iq/disco_info'),
                         self._handle_disco_info))

        self.xmpp.register_handler(
                Callback('Disco Items',
                         StanzaPath('iq/disco_items'),
                         self._handle_disco_items))

        register_stanza_plugin(Iq, DiscoInfo)
        register_stanza_plugin(Iq, DiscoItems)

        self.static = StaticDisco(self.xmpp)

        self._disco_ops = ['get_info', 'set_identities', 'set_features',
                           'get_items', 'set_items', 'del_items',
                           'add_identity', 'del_identity', 'add_feature',
                           'del_feature', 'add_item', 'del_item',
                           'del_identities', 'del_features']
        self._handlers = {}
        for op in self._disco_ops:
            self._handlers[op] = {'global': getattr(self.static, op),
                                  'jid': {},
                                  'node': {}}

    def set_node_handler(self, htype, jid=None, node=None, handler=None):
        """
        Add a node handler for the given hierarchy level and
        handler type.

        Node handlers are ordered in a hierarchy where the
        most specific handler is executed. Thus, a fallback,
        global handler can be used for the majority of cases
        with a few node specific handler that override the
        global behavior.

        Node handler hierarchy:
            JID   | Node  | Level
            ---------------------
            None  | None  | Global
            Given | None  | All nodes for the JID
            None  | Given | Node on self.xmpp.boundjid
            Given | Given | A single node

        Handler types:
            get_info
            get_items
            set_identities
            set_features
            set_items
            del_items
            del_identities
            del_identity
            del_feature
            del_features
            del_item
            add_identity
            add_feature
            add_item

        Arguments:
            htype   -- The operation provided by the handler.
            jid     -- The JID the handler applies to. May be narrowed
                       further if a node is given.
            node    -- The particular node the handler is for. If no JID
                       is given, then the self.xmpp.boundjid.full is
                       assumed.
            handler -- The handler function to use.
        """
        if htype not in self._disco_ops:
            return
        if jid is None and node is None:
            self._handlers[htype]['global'] = handler
        elif node is None:
            self._handlers[htype]['jid'][jid] = handler
        elif jid is None:
            jid = self.xmpp.boundjid.full
            self._handlers[htype]['node'][(jid, node)] = handler
        else:
            self._handlers[htype]['node'][(jid, node)] = handler

    def del_node_handler(self, htype, jid, node):
        """
        Remove a handler type for a JID and node combination.

        The next handler in the hierarchy will be used if one
        exists. If removing the global handler, make sure that
        other handlers exist to process existing nodes.

        Node handler hierarchy:
            JID   | Node  | Level
            ---------------------
            None  | None  | Global
            Given | None  | All nodes for the JID
            None  | Given | Node on self.xmpp.boundjid
            Given | Given | A single node

        Arguments:
            htype -- The type of handler to remove.
            jid   -- The JID from which to remove the handler.
            node  -- The node from which to remove the handler.
        """
        self.set_node_handler(htype, jid, node, None)

    def make_static(self, jid=None, node=None, handlers=None):
        """
        Change all of a node's handlers to the default static
        handlers. Useful for manually overriding the contents
        of a node that would otherwise be handled by a JID level
        or global level dynamic handler.

        Arguments:
            jid      -- The JID owning the node to modify.
            node     -- The node to change to using static handlers.
            handlers -- Optional list of handlers to change to the
                        static version. If provided, only these
                        handlers will be changed. Otherwise, all
                        handlers will use the static version.
        """
        if handlers is None:
            handlers = self._disco_ops
        for op in handlers:
            self.del_node_handler(op, jid, node)
            self.set_node_handler(op, jid, node, getattr(self.static, op))

    def get_info(self, jid=None, node=None, local=False, **kwargs):
        """
        Retrieve the disco#info results from a given JID/node combination.

        Info may be retrieved from both local resources and remote agents;
        the local parameter indicates if the information should be gathered
        by executing the local node handlers, or if a disco#info stanza
        must be generated and sent.

        Arguments:
            jid      -- Request info from this JID.
            node     -- The particular node to query.
            local    -- If true, then the query is for a JID/node
                        combination handled by this Sleek instance and
                        no stanzas need to be sent.
                        Otherwise, a disco stanza must be sent to the
                        remove JID to retrieve the info.
            ifrom    -- Specifiy the sender's JID.
            block    -- If true, block and wait for the stanzas' reply.
            timeout  -- The time in seconds to block while waiting for
                        a reply. If None, then wait indefinitely. The
                        timeout value is only used when block=True.
            callback -- Optional callback to execute when a reply is
                        received instead of blocking and waiting for
                        the reply.
        """
        if local or jid is None:
            log.debug("Looking up local disco#info data " + \
                      "for %s, node %s." % (jid, node))
            info = self._run_node_handler('get_info', jid, node, kwargs)
            return self._fix_default_info(info)

        iq = self.xmpp.Iq()
        # Check dfrom parameter for backwards compatibility
        iq['from'] = kwargs.get('ifrom', kwargs.get('dfrom', ''))
        iq['to'] = jid
        iq['type'] = 'get'
        iq['disco_info']['node'] = node if node else ''
        return iq.send(timeout=kwargs.get('timeout', None),
                       block=kwargs.get('block', None),
                       callback=kwargs.get('callback', None))

    def get_items(self, jid=None, node=None, local=False, **kwargs):
        """
        Retrieve the disco#items results from a given JID/node combination.

        Items may be retrieved from both local resources and remote agents;
        the local parameter indicates if the items should be gathered by
        executing the local node handlers, or if a disco#items stanza must
        be generated and sent.

        Arguments:
            jid      -- Request info from this JID.
            node     -- The particular node to query.
            local    -- If true, then the query is for a JID/node
                        combination handled by this Sleek instance and
                        no stanzas need to be sent.
                        Otherwise, a disco stanza must be sent to the
                        remove JID to retrieve the items.
            ifrom    -- Specifiy the sender's JID.
            block    -- If true, block and wait for the stanzas' reply.
            timeout  -- The time in seconds to block while waiting for
                        a reply. If None, then wait indefinitely.
            callback -- Optional callback to execute when a reply is
                        received instead of blocking and waiting for
                        the reply.
        """
        if local or jid is None:
            return self._run_node_handler('get_items', jid, node, kwargs)

        iq = self.xmpp.Iq()
        # Check dfrom parameter for backwards compatibility
        iq['from'] = kwargs.get('ifrom', kwargs.get('dfrom', ''))
        iq['to'] = jid
        iq['type'] = 'get'
        iq['disco_items']['node'] = node if node else ''
        return iq.send(timeout=kwargs.get('timeout', None),
                       block=kwargs.get('block', None),
                       callback=kwargs.get('callback', None))

    def set_items(self, jid=None, node=None, **kwargs):
        """
        Set or replace all items for the specified JID/node combination.

        The given items must be in a list or set where each item is a
        tuple of the form: (jid, node, name).

        Arguments:
            jid   -- The JID to modify.
            node  -- Optional node to modify.
            items -- A series of items in tuple format.
        """
        self._run_node_handler('set_items', jid, node, kwargs)

    def del_items(self, jid=None, node=None, **kwargs):
        """
        Remove all items from the given JID/node combination.

        Arguments:
            jid  -- The JID to modify.
            node -- Optional node to modify.
        """
        self._run_node_handler('del_items', jid, node, kwargs)

    def add_item(self, jid=None, name='', node=None, subnode='', ijid=None):
        """
        Add a new item element to the given JID/node combination.

        Each item is required to have a JID, but may also specify
        a node value to reference non-addressable entities.

        Arguments:
            jid  -- The JID for the item.
            name  -- Optional name for the item.
            node  -- The node to modify.
            subnode -- Optional node for the item.
            ijid   -- The JID to modify.
        """
        kwargs = {'ijid': jid,
                  'name': name,
                  'inode': subnode}
        self._run_node_handler('add_item', jid, node, kwargs)

    def del_item(self, jid=None, node=None, **kwargs):
        """
        Remove a single item from the given JID/node combination.

        Arguments:
            jid   -- The JID to modify.
            node  -- The node to modify.
            ijid  -- The item's JID.
            inode -- The item's node.
        """
        self._run_node_handler('del_item', jid, node, kwargs)

    def add_identity(self, category='', itype='', name='', node=None, jid=None, lang=None):
        """
        Add a new identity to the given JID/node combination.

        Each identity must be unique in terms of all four identity
        components: category, type, name, and language.

        Multiple, identical category/type pairs are allowed only
        if the xml:lang values are different. Likewise, multiple
        category/type/xml:lang pairs are allowed so long as the
        names are different. A category and type is always required.

        Arguments:
            category -- The identity's category.
            itype    -- The identity's type.
            name     -- Optional name for the identity.
            lang     -- Optional two-letter language code.
            node     -- The node to modify.
            jid      -- The JID to modify.
        """
        kwargs = {'category': category,
                  'itype': itype,
                  'name': name,
                  'lang': lang}
        self._run_node_handler('add_identity', jid, node, kwargs)

    def add_feature(self, feature, node=None, jid=None):
        """
        Add a feature to a JID/node combination.

        Arguments:
            feature -- The namespace of the supported feature.
            node    -- The node to modify.
            jid     -- The JID to modify.
        """
        kwargs = {'feature': feature}
        self._run_node_handler('add_feature', jid, node, kwargs)

    def del_identity(self, jid=None, node=None, **kwargs):
        """
        Remove an identity from the given JID/node combination.

        Arguments:
            jid      -- The JID to modify.
            node     -- The node to modify.
            category -- The identity's category.
            itype    -- The identity's type value.
            name     -- Optional, human readable name for the identity.
            lang     -- Optional, the identity's xml:lang value.
        """
        self._run_node_handler('del_identity', jid, node, kwargs)

    def del_feature(self, jid=None, node=None, **kwargs):
        """
        Remove a feature from a given JID/node combination.

        Arguments:
            jid     -- The JID to modify.
            node    -- The node to modify.
            feature -- The feature's namespace.
        """
        self._run_node_handler('del_feature', jid, node, kwargs)

    def set_identities(self, jid=None, node=None, **kwargs):
        """
        Add or replace all identities for the given JID/node combination.

        The identities must be in a set where each identity is a tuple
        of the form: (category, type, lang, name)

        Arguments:
            jid        -- The JID to modify.
            node       -- The node to modify.
            identities -- A set of identities in tuple form.
            lang       -- Optional, xml:lang value.
        """
        self._run_node_handler('set_identities', jid, node, kwargs)

    def del_identities(self, jid=None, node=None, **kwargs):
        """
        Remove all identities for a JID/node combination.

        If a language is specified, only identities using that
        language will be removed.

        Arguments:
            jid  -- The JID to modify.
            node -- The node to modify.
            lang -- Optional. If given, only remove identities
                    using this xml:lang value.
        """
        self._run_node_handler('del_identities', jid, node, kwargs)

    def set_features(self, jid=None, node=None, **kwargs):
        """
        Add or replace the set of supported features
        for a JID/node combination.

        Arguments:
            jid      -- The JID to modify.
            node     -- The node to modify.
            features -- The new set of supported features.
        """
        self._run_node_handler('set_features', jid, node, kwargs)

    def del_features(self, jid=None, node=None, **kwargs):
        """
        Remove all features from a JID/node combination.

        Arguments:
            jid  -- The JID to modify.
            node -- The node to modify.
        """
        self._run_node_handler('del_features', jid, node, kwargs)

    def _run_node_handler(self, htype, jid, node, data={}):
        """
        Execute the most specific node handler for the given
        JID/node combination.

        Arguments:
            htype -- The handler type to execute.
            jid   -- The JID requested.
            node  -- The node requested.
            data  -- Optional, custom data to pass to the handler.
        """
        if jid is None:
            jid = self.xmpp.boundjid.full
        if node is None:
            node = ''

        if self._handlers[htype]['node'].get((jid, node), False):
            return self._handlers[htype]['node'][(jid, node)](jid, node, data)
        elif self._handlers[htype]['jid'].get(jid, False):
            return self._handlers[htype]['jid'][jid](jid, node, data)
        elif self._handlers[htype]['global']:
            return self._handlers[htype]['global'](jid, node, data)
        else:
            return None

    def _handle_disco_info(self, iq):
        """
        Process an incoming disco#info stanza. If it is a get
        request, find and return the appropriate identities
        and features. If it is an info result, fire the
        disco_info event.

        Arguments:
            iq -- The incoming disco#items stanza.
        """
        if iq['type'] == 'get':
            log.debug("Received disco info query from " + \
                      "<%s> to <%s>." % (iq['from'], iq['to']))
            info = self._run_node_handler('get_info',
                                          iq['to'].full,
                                          iq['disco_info']['node'],
                                          iq)
            iq.reply()
            if info:
                info = self._fix_default_info(info)
                iq.set_payload(info.xml)
            iq.send()
        elif iq['type'] == 'result':
            log.debug("Received disco info result from" + \
                      "%s to %s." % (iq['from'], iq['to']))
            self.xmpp.event('disco_info', iq)

    def _handle_disco_items(self, iq):
        """
        Process an incoming disco#items stanza. If it is a get
        request, find and return the appropriate items. If it
        is an items result, fire the disco_items event.

        Arguments:
            iq -- The incoming disco#items stanza.
        """
        if iq['type'] == 'get':
            log.debug("Received disco items query from " + \
                      "<%s> to <%s>." % (iq['from'], iq['to']))
            items = self._run_node_handler('get_items',
                                          iq['to'].full,
                                          iq['disco_items']['node'])
            iq.reply()
            if items:
                iq.set_payload(items.xml)
            iq.send()
        elif iq['type'] == 'result':
            log.debug("Received disco items result from" + \
                      "%s to %s." % (iq['from'], iq['to']))
            self.xmpp.event('disco_items', iq)

    def _fix_default_info(self, info):
        """
        Disco#info results for a JID are required to include at least
        one identity and feature. As a default, if no other identity is
        provided, SleekXMPP will use either the generic component or the
        bot client identity. A the standard disco#info feature will also be
        added if no features are provided.

        Arguments:
            info -- The disco#info quest (not the full Iq stanza) to modify.
        """
        if not info['node']:
            if not info['identities']:
                if self.xmpp.is_component:
                    log.debug("No identity found for this entity." + \
                              "Using default component identity.")
                    info.add_identity('component', 'generic')
                else:
                    log.debug("No identity found for this entity." + \
                              "Using default client identity.")
                    info.add_identity('client', 'bot')
            if not info['features']:
                log.debug("No features found for this entity." + \
                          "Using default disco#info feature.")
                info.add_feature(info.namespace)
        return info
