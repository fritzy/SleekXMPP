"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.xmlstream import JID
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.plugins.xep_0060 import stanza


log = logging.getLogger(__name__)


class xep_0060(base_plugin):

    """
    XEP-0060 Publish Subscribe
    """

    def plugin_init(self):
        self.xep = '0060'
        self.description = 'Publish-Subscribe'
        self.stanza = stanza

    def create_node(self, jid, node, config=None, ntype=None, ifrom=None,
                    block=True, callback=None, timeout=None):
        """
        Create and configure a new pubsub node.

        A server MAY use a different name for the node than the one provided,
        so be sure to check the result stanza for a server assigned name.

        If no configuration form is provided, the node will be created using
        the server's default configuration. To get the default configuration
        use get_node_config().

        Arguments:
            jid      -- The JID of the pubsub service.
            node     -- Optional name of the node to create. If no name is
                        provided, the server MAY generate a node ID for you.
                        The server can also assign a different name than the
                        one you provide; check the result stanza to see if
                        the server assigned a name.
            config   -- Optional XEP-0004 data form of configuration settings.
            ntype    -- The type of node to create. Servers typically default
                        to using 'leaf' if no type is provided.
            ifrom    -- Specify the sender's JID.
            block    -- Specify if the send call will block until a response
                        is received, or a timeout occurs. Defaults to True.
            timeout  -- The length of time (in seconds) to wait for a response
                        before exiting the send call if blocking is used.
                        Defaults to sleekxmpp.xmlstream.RESPONSE_TIMEOUT
            callback -- Optional reference to a stream handler function. Will
                        be executed when a reply stanza is received.
        """
        iq = self.xmpp.Iq(sto=jid, sfrom=ifrom, stype='set')
        iq['pubsub']['create']['node'] = node

        if config is not None:
            form_type = 'http://jabber.org/protocol/pubsub#node_config'
            if 'FORM_TYPE' in config['fields']:
                config.field['FORM_TYPE']['value'] = form_type
            else:
                config.add_field(var='FORM_TYPE',
                                 ftype='hidden',
                                 value=form_type)
            if ntype:
                if 'pubsub#node_type' in config['fields']:
                    config.field['pubsub#node_type']['value'] = ntype
                else:
                    config.add_field(var='pubsub#node_type', value=ntype)
            iq['pubsub']['configure'].append(config)

        return iq.send(block=block, callback=callback, timeout=timeout)

    def subscribe(self, jid, node, bare=True, subscribee=None, options=None,
                  ifrom=None, block=True, callback=None, timeout=None):
        """
        Subscribe to updates from a pubsub node.

        The rules for determining the JID that is subscribing to the node are:
            1. If subscribee is given, use that as provided.
            2. If ifrom was given, use the bare or full version based on bare.
            3. Otherwise, use self.xmpp.boundjid based on bare.

        Arguments:
            jid        -- The pubsub service JID.
            node       -- The node to subscribe to.
            bare       -- Indicates if the subscribee is a bare or full JID.
                          Defaults to True for a bare JID.
            subscribee -- The JID that is subscribing to the node.
            options    --
            ifrom      -- Specify the sender's JID.
            block      -- Specify if the send call will block until a response
                          is received, or a timeout occurs. Defaults to True.
            timeout    -- The length of time (in seconds) to wait for a response
                          before exiting the send call if blocking is used.
                          Defaults to sleekxmpp.xmlstream.RESPONSE_TIMEOUT
            callback   -- Optional reference to a stream handler function. Will
                          be executed when a reply stanza is received.
        """
        iq = self.xmpp.Iq(sto=jid, sfrom=ifrom, stype='set')
        iq['pubsub']['subscribe']['node'] = node

        if subscribee is None:
            if ifrom:
                if bare:
                    subscribee = JID(ifrom).bare
                else:
                    subscribee = ifrom
            else:
                if bare:
                    subscribee = self.xmpp.boundjid.bare
                else:
                    subscribee = self.xmpp.boundjid

        iq['pubsub']['subscribe']['jid'] = subscribee
        return iq.send(block=block, callback=callback, timeout=timeout)

    def unsubscribe(self, jid, node, subid=None, bare=True, subscribee=None,
                    ifrom=None, block=True, callback=None, timeout=None):
        """
        Unubscribe from updates from a pubsub node.

        The rules for determining the JID that is unsubscribing
        from the node are:
            1. If subscribee is given, use that as provided.
            2. If ifrom was given, use the bare or full version based on bare.
            3. Otherwise, use self.xmpp.boundjid based on bare.

        Arguments:
            jid        -- The pubsub service JID.
            node       -- The node to subscribe to.
            subid      -- The specific subscription, if multiple subscriptions
                          exist for this JID/node combination.
            bare       -- Indicates if the subscribee is a bare or full JID.
                          Defaults to True for a bare JID.
            subscribee -- The JID that is subscribing to the node.
            ifrom      -- Specify the sender's JID.
            block      -- Specify if the send call will block until a response
                          is received, or a timeout occurs. Defaults to True.
            timeout    -- The length of time (in seconds) to wait for a response
                          before exiting the send call if blocking is used.
                          Defaults to sleekxmpp.xmlstream.RESPONSE_TIMEOUT
            callback   -- Optional reference to a stream handler function. Will
                          be executed when a reply stanza is received.
        """
        iq = self.xmpp.Iq(sto=jid, sfrom=ifrom, stype='set')
        iq['pubsub']['unsubscribe']['node'] = node

        if subscribee is None:
            if ifrom:
                if bare:
                    subscribee = JID(ifrom).bare
                else:
                    subscribee = ifrom
            else:
                if bare:
                    subscribee = self.xmpp.boundjid.bare
                else:
                    subscribee = self.xmpp.boundjid

        iq['pubsub']['unsubscribe']['jid'] = subscribee
        iq['pubsub']['unsubscribe']['subid'] = subid
        return iq.send(block=block, callback=callback, timeout=timeout)

    def get_subscription_options(self):
        pass

    def set_subscription_options(self):
        pass

    def get_node_config(self, jid, node=None, ifrom=None, block=None,
                        callback=None, timeout=None):
        """
        Retrieve the configuration for a node, or the pubsub service's
        default configuration for new nodes.

        Arguments:
            jid      -- The JID of the pubsub service.
            node     -- The node to retrieve the configuration for. If None,
                        the default configuration for new nodes will be
                        requested. Defaults to None.
            ifrom    -- Specify the sender's JID.
            block    -- Specify if the send call will block until a response
                        is received, or a timeout occurs. Defaults to True.
            timeout  -- The length of time (in seconds) to wait for a response
                        before exiting the send call if blocking is used.
                        Defaults to sleekxmpp.xmlstream.RESPONSE_TIMEOUT
            callback -- Optional reference to a stream handler function. Will
                        be executed when a reply stanza is received.
        """
        iq = self.xmpp.Iq(sto=jid, sfrom=ifrom, stype='get')

        if node is None:
            iq['pubsub_owner']['default']
        else:
            iq['pubsub_owner']['configure']['node'] = node
        return iq.send(block=block, callback=callback, timeout=timeout)

    def get_node_subscriptions(self, jid, node, ifrom=None, block=True,
                               callback=None, timeout=None):
        """
        Retrieve the subscriptions associated with a given node.

        Arguments:
            jid      -- The JID of the pubsub service.
            node     -- The node to retrieve subscriptions from.
            ifrom    -- Specify the sender's JID.
            block    -- Specify if the send call will block until a response
                        is received, or a timeout occurs. Defaults to True.
            timeout  -- The length of time (in seconds) to wait for a response
                        before exiting the send call if blocking is used.
                        Defaults to sleekxmpp.xmlstream.RESPONSE_TIMEOUT
            callback -- Optional reference to a stream handler function. Will
                        be executed when a reply stanza is received.
        """
        iq = self.xmpp.Iq(sto=jid, sfrom=ifrom, stype='get')
        iq['pubsub_owner']['subscriptions']['node'] = node
        return iq.send(block=block, callback=callback, timeout=timeout)

    def get_node_affiliations(self, jid, node, ifrom=None, block=True,
                              callback=None, timeout=None):
        """
        Retrieve the affiliations associated with a given node.

        Arguments:
            jid      -- The JID of the pubsub service.
            node     -- The node to retrieve affiliations from.
            ifrom    -- Specify the sender's JID.
            block    -- Specify if the send call will block until a response
                        is received, or a timeout occurs. Defaults to True.
            timeout  -- The length of time (in seconds) to wait for a response
                        before exiting the send call if blocking is used.
                        Defaults to sleekxmpp.xmlstream.RESPONSE_TIMEOUT
            callback -- Optional reference to a stream handler function. Will
                        be executed when a reply stanza is received.
        """
        iq = self.xmpp.Iq(sto=jid, sfrom=ifrom, stype='get')
        iq['pubsub_owner']['affiliations']['node'] = node
        return iq.send(block=block, callback=callback, timeout=timeout)

    def delete_node(self, jid, node, ifrom=None, block=True,
                    callback=None, timeout=None):
        """
        Delete a a pubsub node.

        Arguments:
            jid      -- The JID of the pubsub service.
            node     -- The node to delete.
            ifrom    -- Specify the sender's JID.
            block    -- Specify if the send call will block until a response
                        is received, or a timeout occurs. Defaults to True.
            timeout  -- The length of time (in seconds) to wait for a response
                        before exiting the send call if blocking is used.
                        Defaults to sleekxmpp.xmlstream.RESPONSE_TIMEOUT
            callback -- Optional reference to a stream handler function. Will
                        be executed when a reply stanza is received.
        """
        iq = self.xmpp.Iq(sto=jid, sfrom=ifrom, stype='get')
        iq['pubsub_owner']['delete']['node'] = node
        return iq.send(block=block, callback=callback, timeout=timeout)

    def set_node_config(self, jid, node, config, ifrom=None, block=True,
                        callback=None, timeout=None):
        iq = self.xmpp.Iq(sto=jid, sfrom=ifrom, stype='set')
        iq['pubsub_owner']['configure']['node'] = node
        iq['pubsub_owner']['configure']['config'] = config
        return iq.send(block=block, callback=callback, timeout=timeout)

    def publish(self, jid, node, items=[], ifrom=None, block=True,
                callback=None, timeout=None):
        iq = self.xmpp.Iq(sto=jid, sfrom=ifrom, stype='set')
        iq['pubsub']['publish']['node'] = node
        for id, payload in items:
            item = stanza.pubsub.Item()
            if id is not None:
                item['id'] = id
            item['payload'] = payload
            iq['pubsub']['publish'].append(item)
        return iq.send(block=block, callback=callback, timeout=timeout)

    def retract(self, jid, node, item, ifrom=None, block=True,
                callback=None, timeout=None):
        iq = self.xmpp.Iq(sto=jid, sfrom=ifrom, stype='set')

        iq['pubsub']['retract']['node'] = node
        item = stanza.pubsub.Item()
        item['id'] = item
        iq['pubsub']['retract'].append(item)
        return iq.send(block=block, callback=callback, timeout=timeout)

    def purge(self, jid, node, ifrom=None, block=True, callback=None,
              timeout=None):
        iq = self.xmpp.Iq(sto=jid, sfrom=ifrom, stype='set')
        iq['pubsub']['purge']['node'] = node
        return iq.send(block=block, callback=callback, timeout=timeout)

    def get_nodes(self, *args, **kwargs):
        return self.xmpp.plugin['xep_0040'].get_items(*args, **kwargs)

    def get_item(self):
        pass

    def get_items(self, jid, node, ifrom=None, block=True,
                  callback=None, timeout=None, iterator=False):
        return self.xmpp.plugin['xep_0030'].get_items(jid, node,
                                                      ifrom=ifrom,
                                                      block=block,
                                                      callback=callback,
                                                      timeout=timeout,
                                                      iterator=iterator)

    def modify_affiliation(self, jid, node, affiliation, user_jid=None,
                           ifrom=None, block=True, callback=None,
                           timeout=None):
        iq = self.xmpp.Iq(sto=jid, sfrom=ifrom, stype='set')

        iq['pubsub_owner']['affiliations']
        aff = stanza.pubsub.Affiliation()
        aff['node'] = node
        if user_jid is not None:
            aff['jid'] = user_jid
        aff['affiliation'] = affiliation
        iq['pubsub_owner']['affiliations'].append(aff)
        return iq.send(block=block, callback=callback, timeout=timeout)

    def modify_subscription(self):
        pass

    def purge(self):
        pass
