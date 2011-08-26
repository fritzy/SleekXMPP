"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

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
        iq = self.xmpp.Iq(sto=jid, stype='set')
        if ifrom:
            iq['from'] = ifrom
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

    def subscribe(self, jid, node, bare=True, subscribee=None):
        iq = self.xmpp.Iq(sto=jid, sfrom=self.xmpp.boundjid, stype='set')
        iq['pubsub']['subscribe']['node'] = node
        if subscribee is None:
            if bare:
                iq['pubsub']['subscribe']['jid'] = self.xmpp.boundjid.bare
            else:
                iq['pubsub']['subscribe']['jid'] = self.xmpp.boundjid.full
        else:
            iq['pubsub']['subscribe']['jid'] = subscribee
        return iq.send()

    def unsubscribe(self, jid, node, subid=None, bare=True, subscribee=None):
        iq = self.xmpp.Iq(sto=jid, sfrom=self.xmpp.boundjid, stype='set')
        iq['pubsub']['unsubscribe']['node'] = node
        if subscribee is None:
            if bare:
                iq['pubsub']['unsubscribe']['jid'] = self.xmpp.boundjid.bare
            else:
                iq['pubsub']['unsubscribe']['jid'] = self.xmpp.boundjid.full
        else:
            iq['pubsub']['unsubscribe']['jid'] = subscribee
        if subid is not None:
            iq['pubsub']['unsubscribe']['subid'] = subid
        return iq.send()

    def get_node_config(self, jid, node=None): # if no node, then grab default
        iq = self.xmpp.Iq(sto=jid, sfrom=self.xmpp.boundjid, stype='get')
        if node is None:
            iq['pubsub_owner']['default']
        else:
            iq['pubsub_owner']['configure']['node'] = node
        return iq.send()

    def get_node_subscriptions(self, jid, node):
        iq = self.xmpp.Iq(sto=jid, sfrom=self.xmpp.boundjid, stype='get')
        iq['pubsub_owner']['subscriptions']['node'] = node
        return iq.send()

    def get_node_affiliations(self, jid, node):
        iq = self.xmpp.Iq(sto=jid, sfrom=self.xmpp.boundjid, stype='get')
        iq['pubsub_owner']['affiliations']['node'] = node
        return iq.send()

    def delete_node(self, jid, node):
        iq = self.xmpp.Iq(sto=jid, sfrom=self.xmpp.boundjid, stype='get')
        iq['pubsub_owner']['delete']['node'] = node
        return iq.send()

    def set_node_config(self, jid, node, config):
        iq = self.xmpp.Iq(sto=jid, sfrom=self.xmpp.boundjid, stype='set')
        iq['pubsub_owner']['configure']['node'] = node
        iq['pubsub_owner']['configure']['config'] = config
        return iq.send()

    def publish(self, jid, node, items=[]):
        iq = self.xmpp.Iq(sto=jid, sfrom=self.xmpp.boundjid, stype='set')
        iq['pubsub']['publish']['node'] = node
        for id, payload in items:
            item = stanza.pubsub.Item()
            if id is not None:
                item['id'] = id
            item['payload'] = payload
            iq['pubsub']['publish'].append(item)
        return iq.send()

    def retract(self, jid, node, item):
        iq = self.xmpp.Iq(sto=jid, sfrom=self.xmpp.boundjid, stype='set')
        iq['pubsub']['retract']['node'] = node
        item = stanza.pubsub.Item()
        item['id'] = item
        iq['pubsub']['retract'].append(item)
        return iq.send()

    def get_nodes(self, jid):
        return self.xmpp.plugin['xep_0030'].get_items(jid)

    def getItems(self, jid, node):
        return self.xmpp.plugin['xep_0030'].get_items(jid, node)

    def modify_affiliation(self, jid, node, affiliation, user_jid=None):
        iq = self.xmpp.Iq(sto=jid, sfrom=self.xmpp.boundjid, stype='set')
        iq['pubsub_owner']['affiliations']
        aff = stanza.pubsub.Affiliation()
        aff['node'] = node
        if user_jid is not None:
            aff['jid'] = user_jid
        aff['affiliation'] = affiliation
        iq['pubsub_owner']['affiliations'].append(aff)
        return iq.send()
