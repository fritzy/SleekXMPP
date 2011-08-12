from __future__ import with_statement
from sleekxmpp.plugins import base
import logging
#from xml.etree import cElementTree as ET
from sleekxmpp.xmlstream.stanzabase import registerStanzaPlugin, ElementBase, ET
from sleekxmpp.plugins.xep_0060 import stanza
from sleekxmpp.plugins.xep_0004 import Form


log = logging.getLogger(__name__)


class xep_0060(base.base_plugin):
    """
    XEP-0060 Publish Subscribe
    """

    def plugin_init(self):
        self.xep = '0060'
        self.description = 'Publish-Subscribe'

    def create_node(self, jid, node, config=None, ntype=None):
        iq = IQ(sto=jid, stype='set', sfrom=self.xmpp.jid)
        iq['pubsub']['create']['node'] = node
        if ntype is None:
            ntype = 'leaf'
        if config is not None:
            if 'FORM_TYPE' in submitform.field:
                config.field['FORM_TYPE'].setValue('http://jabber.org/protocol/pubsub#node_config')
            else:
                config.addField('FORM_TYPE', 'hidden', value='http://jabber.org/protocol/pubsub#node_config')
            if 'pubsub#node_type' in submitform.field:
                config.field['pubsub#node_type'].setValue(ntype)
            else:
                config.addField('pubsub#node_type', value=ntype)
            iq['pubsub']['configure']['form'] = config
        return iq.send()

    def subscribe(self, jid, node, bare=True, subscribee=None):
        iq = IQ(sto=jid, sfrom=self.xmpp.jid, stype='set')
        iq['pubsub']['subscribe']['node'] = node
        if subscribee is None:
            if bare:
                iq['pubsub']['subscribe']['jid'] = self.xmpp.jid.bare
            else:
                iq['pubsub']['subscribe']['jid'] = self.xmpp.jid.full
        else:
            iq['pubsub']['subscribe']['jid'] = subscribee
        return iq.send()

    def unsubscribe(self, jid, node, subid=None, bare=True, subscribee=None):
        iq = IQ(sto=jid, sfrom=self.xmpp.jid, stype='set')
        iq['pubsub']['unsubscribe']['node'] = node
        if subscribee is None:
            if bare:
                iq['pubsub']['unsubscribe']['jid'] = self.xmpp.jid.bare
            else:
                iq['pubsub']['unsubscribe']['jid'] = self.xmpp.jid.full
        else:
            iq['pubsub']['unsubscribe']['jid'] = subscribee
        if subid is not None:
            iq['pubsub']['unsubscribe']['subid'] = subid
        return iq.send()

    def get_node_config(self, jid, node=None): # if no node, then grab default
        iq = IQ(sto=jid, sfrom=self.xmpp.jid, stype='get')
        if node is None:
            iq['pubsub_owner']['default']
        else:
            iq['pubsub_owner']['configure']['node'] = node
        return iq.send()

    def get_node_subscriptions(self, jid, node):
        iq = IQ(sto=jid, sfrom=self.xmpp.jid, stype='get')
        iq['pubsub_owner']['subscriptions']['node'] = node
        return iq.send()

    def get_node_affiliations(self, jid, node):
        iq = IQ(sto=jid, sfrom=self.xmpp.jid, stype='get')
        iq['pubsub_owner']['affiliations']['node'] = node
        return iq.send()

    def delete_node(self, jid, node):
        iq = IQ(sto=jid, sfrom=self.xmpp.jid, stype='get')
        iq['pubsub_owner']['delete']['node'] = node
        return iq.send()

    def set_node_config(self, jid, node, config):
        iq = IQ(sto=jid, sfrom=self.xmpp.jid, stype='set')
        iq['pubsub_owner']['configure']['node'] = node
        iq['pubsub_owner']['configure']['config'] = config
        return iq.send()

    def publish(self, jid, node, items=[]):
        iq = IQ(sto=jid, sfrom=self.xmpp.jid, stype='set')
        iq['pubsub']['publish']['node'] = node
        for id, payload in items:
            item = stanza.pubsub.Item()
            if id is not None:
                item['id'] = id
            item['payload'] = payload
            iq['pubsub']['publish'].append(item)
        return iq.send()

    def retract(self, jid, node, item):
        iq = IQ(sto=jid, sfrom=self.xmpp.jid, stype='set')
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
        iq = IQ(sto=jid, sfrom=self.xmpp.jid, stype='set')
        iq['pubsub_owner']['affiliations']
        aff = stanza.pubsub.Affiliation()
        aff['node'] = node
        if user_jid is not None:
            aff['jid'] = user_jid
        aff['affiliation'] = affiliation
        iq['pubsub_owner']['affiliations'].append(aff)
        return iq.send()
