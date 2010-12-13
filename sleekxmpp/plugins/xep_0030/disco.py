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

    Methods:
        set_node_handler --
        del_node_handler --
        add_identity     --
        del_identity     --
        add_feature      --
        del_feature      --
        add_item         --
        del_item         --
        get_info         --
        get_items        --
    """

    def plugin_init(self):
        self.xep = '0030'
        self.description = 'Service Discovery'
        self.stanza = sleekxmpp.plugins.xep_0030.stanza

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
                           'del_info', 'get_items', 'set_items', 'del_items',
                           'add_identity', 'del_identity', 'add_feature',
                           'del_feature', 'add_item', 'del_item']
        self.handlers = {}
        for op in self._disco_ops:
            self.handlers[op] = {'global': getattr(self.static, op),
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
            del_info
            del_items
            del_identity
            del_feature
            del_item
            add_identity
            add_feature
            add_item
 
        Arguments:
            htype   -- The operation provided by the handler.
            jid     --
            node    --
            handler --
        """
        if htype not in self._disco_ops:
            return
        if jid is None and node is None:
            self.handlers[htype]['global'] = handler
        elif node is None:
            self.handlers[htype]['jid'][jid] = handler
        elif jid is None:
            jid = self.xmpp.boundjid.full
            self.handlers[htype]['node'][(jid, node)] = handler
        else:
            self.handlers[htype]['node'][(jid, node)] = handler

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
        Arguments:
            jid      --
            node     --
            local    --
            dfrom    --
            block    --
            timeout  --
            callback --
        """
        if local or jid is None:
            log.debug("Looking up local disco#info data " + \
                      "for %s, node %s." % (jid, node))
            info = self._run_node_handler('get_info', jid, node, kwargs)
            return self._fix_default_info(info)

        iq = self.xmpp.Iq()
        iq['from'] = kwargs.get('dfrom', '')
        iq['to'] = jid
        iq['type'] = 'get'
        iq['disco_info']['node'] = node if node else ''
        return iq.send(timeout=kwargs.get('timeout', None),
                       block=kwargs.get('block', None),
                       callback=kwargs.get('callback', None))

    def get_items(self, jid=None, node=None, local=False, **kwargs):
        """
        Arguments:
            jid      --
            node     --
            local    --
            dfrom    --
            block    --
            timeout  --
            callback --
        """
        if local or jid is None:
            return self._run_node_handler('get_items', jid, node, kwargs)

        iq = self.xmpp.Iq()
        iq['from'] = kwargs.get('dfrom', '')
        iq['to'] = jid
        iq['type'] = 'get'
        iq['disco_items']['node'] = node if node else ''
        return iq.send(timeout=kwargs.get('timeout', None),
                       block=kwargs.get('block', None),
                       callback=kwargs.get('callback', None))

    def set_info(self, jid=None, node=None, **kwargs):
        self._run_node_handler('set_info', jid, node, kwargs)

    def del_info(self, jid=None, node=None, **kwargs):
        self._run_node_handler('del_info', jid, node, kwargs)

    def set_items(self, jid=None, node=None, **kwargs):
        self._run_node_handler('set_items', jid, node, kwargs)

    def del_items(self, jid=None, node=None, **kwargs):
        self._run_node_handler('del_items', jid, node, kwargs)

    def add_identity(self, jid=None, node=None, **kwargs):
        self._run_node_handler('add_identity', jid, node, kwargs)

    def add_feature(self, jid=None, node=None, **kwargs):
        self._run_node_handler('add_feature', jid, node, kwargs)

    def del_identity(self, jid=None, node=None, **kwargs):
        self._run_node_handler('del_identity', jid, node, kwargs)

    def del_feature(self, jid=None, node=None, **kwargs):
        self._run_node_handler('del_feature', jid, node, kwargs)

    def add_item(self, jid=None, node=None, **kwargs):
        self._run_node_handler('add_item', jid, node, kwargs)

    def del_item(self, jid=None, node=None, **kwargs):
        self._run_node_handler('del_item', jid, node, kwargs)

    def _run_node_handler(self, htype, jid, node, data=None):
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

        if self.handlers[htype]['node'].get((jid, node), False):
            return self.handlers[htype]['node'][(jid, node)](jid, node, data)
        elif self.handlers[htype]['jid'].get(jid, False):
            return self.handlers[htype]['jid'][jid](jid, node, data)
        elif self.handlers[htype]['global']:
            return self.handlers[htype]['global'](jid, node, data)
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
