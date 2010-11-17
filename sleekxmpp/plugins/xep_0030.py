"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging
from . import base
from .. xmlstream.handler.callback import Callback
from .. xmlstream.matcher.xpath import MatchXPath
from .. xmlstream.stanzabase import registerStanzaPlugin, ElementBase, ET, JID
from .. stanza.iq import Iq


log = logging.getLogger(__name__)


class DiscoInfo(ElementBase):
    namespace = 'http://jabber.org/protocol/disco#info'
    name = 'query'
    plugin_attrib = 'disco_info'
    interfaces = set(('node', 'features', 'identities'))

    def getFeatures(self):
        features = []
        featuresXML = self.xml.findall('{%s}feature' % self.namespace)
        for feature in featuresXML:
            features.append(feature.attrib['var'])
        return features

    def setFeatures(self, features):
        self.delFeatures()
        for name in features:
            self.addFeature(name)

    def delFeatures(self):
        featuresXML = self.xml.findall('{%s}feature' % self.namespace)
        for feature in featuresXML:
            self.xml.remove(feature)

    def addFeature(self, feature):
        featureXML = ET.Element('{%s}feature' % self.namespace,
                    {'var': feature})
        self.xml.append(featureXML)

    def delFeature(self, feature):
        featuresXML = self.xml.findall('{%s}feature' % self.namespace)
        for featureXML in featuresXML:
            if featureXML.attrib['var'] == feature:
                self.xml.remove(featureXML)

    def getIdentities(self):
        ids = []
        idsXML = self.xml.findall('{%s}identity' % self.namespace)
        for idXML in idsXML:
            idData = (idXML.attrib['category'],
                  idXML.attrib['type'],
                  idXML.attrib.get('name', ''))
            ids.append(idData)
        return ids

    def setIdentities(self, ids):
        self.delIdentities()
        for idData in ids:
            self.addIdentity(*idData)

    def delIdentities(self):
        idsXML = self.xml.findall('{%s}identity' % self.namespace)
        for idXML in idsXML:
            self.xml.remove(idXML)

    def addIdentity(self, category, id_type, name=''):
        idXML = ET.Element('{%s}identity' % self.namespace,
                   {'category': category,
                    'type': id_type,
                    'name': name})
        self.xml.append(idXML)

    def delIdentity(self, category, id_type, name=''):
        idsXML = self.xml.findall('{%s}identity' % self.namespace)
        for idXML in idsXML:
            idData = (idXML.attrib['category'],
                  idXML.attrib['type'])
            delId = (category, id_type)
            if idData == delId:
                self.xml.remove(idXML)


class DiscoItems(ElementBase):
    namespace = 'http://jabber.org/protocol/disco#items'
    name = 'query'
    plugin_attrib = 'disco_items'
    interfaces = set(('node', 'items'))

    def getItems(self):
        items = []
        itemsXML = self.xml.findall('{%s}item' % self.namespace)
        for item in itemsXML:
            itemData = (item.attrib['jid'],
                    item.attrib.get('node'),
                    item.attrib.get('name'))
            items.append(itemData)
        return items

    def setItems(self, items):
        self.delItems()
        for item in items:
            self.addItem(*item)

    def delItems(self):
        itemsXML = self.xml.findall('{%s}item' % self.namespace)
        for item in itemsXML:
            self.xml.remove(item)

    def addItem(self, jid, node='', name=''):
        itemXML = ET.Element('{%s}item' % self.namespace, {'jid': jid})
        if name:
            itemXML.attrib['name'] = name
        if node:
            itemXML.attrib['node'] = node
        self.xml.append(itemXML)

    def delItem(self, jid, node=''):
        itemsXML = self.xml.findall('{%s}item' % self.namespace)
        for itemXML in itemsXML:
            itemData = (itemXML.attrib['jid'],
                    itemXML.attrib.get('node', ''))
            itemDel = (jid, node)
            if itemData == itemDel:
                self.xml.remove(itemXML)


class DiscoNode(object):
    """
    Collection object for grouping info and item information
    into nodes.
    """
    def __init__(self, name):
        self.name = name
        self.info = DiscoInfo()
        self.items = DiscoItems()

        self.info['node'] = name
        self.items['node'] = name

        # This is a bit like poor man's inheritance, but
        # to simplify adding information to the node we
        # map node functions to either the info or items
        # stanza objects.
        #
        # We don't want to make DiscoNode inherit from
        # DiscoInfo and DiscoItems because DiscoNode is
        # not an actual stanza, and doing so would create
        # confusion and potential bugs.

        self._map(self.items, 'items', ['get', 'set', 'del'])
        self._map(self.items, 'item', ['add', 'del'])
        self._map(self.info, 'identities', ['get', 'set', 'del'])
        self._map(self.info, 'identity', ['add', 'del'])
        self._map(self.info, 'features', ['get', 'set', 'del'])
        self._map(self.info, 'feature', ['add', 'del'])

    def isEmpty(self):
        """
        Test if the node contains any information. Useful for
        determining if a node can be deleted.
        """
        ids = self.getIdentities()
        features = self.getFeatures()
        items = self.getItems()

        if not ids and not features and not items:
            return True
        return False

    def _map(self, obj, interface, access):
        """
        Map functions of the form obj.accessInterface
        to self.accessInterface for each given access type.
        """
        interface = interface.title()
        for access_type in access:
            method = access_type + interface
            if hasattr(obj, method):
                setattr(self, method, getattr(obj, method))


class xep_0030(base.base_plugin):
    """
    XEP-0030 Service Discovery
    """

    def plugin_init(self):
        self.xep = '0030'
        self.description = 'Service Discovery'

        self.xmpp.registerHandler(
            Callback('Disco Items',
                 MatchXPath('{%s}iq/{%s}query' % (self.xmpp.default_ns,
                                  DiscoItems.namespace)),
                 self.handle_item_query))

        self.xmpp.registerHandler(
            Callback('Disco Info',
                 MatchXPath('{%s}iq/{%s}query' % (self.xmpp.default_ns,
                                  DiscoInfo.namespace)),
                 self.handle_info_query))

        registerStanzaPlugin(Iq, DiscoInfo)
        registerStanzaPlugin(Iq, DiscoItems)

        self.xmpp.add_event_handler('disco_items_request', self.handle_disco_items)
        self.xmpp.add_event_handler('disco_info_request', self.handle_disco_info)

        self.nodes = {'main': DiscoNode('main')}

    def add_node(self, node):
        if node not in self.nodes:
            self.nodes[node] = DiscoNode(node)

    def del_node(self, node):
        if node in self.nodes:
            del self.nodes[node]

    def handle_item_query(self, iq):
        if iq['type'] == 'get':
            log.debug("Items requested by %s" % iq['from'])
            self.xmpp.event('disco_items_request', iq)
        elif iq['type'] == 'result':
            log.debug("Items result from %s" % iq['from'])
            self.xmpp.event('disco_items', iq)

    def handle_info_query(self, iq):
        if iq['type'] == 'get':
            log.debug("Info requested by %s" % iq['from'])
            self.xmpp.event('disco_info_request', iq)
        elif iq['type'] == 'result':
            log.debug("Info result from %s" % iq['from'])
            self.xmpp.event('disco_info', iq)

    def handle_disco_info(self, iq, forwarded=False):
        """
        A default handler for disco#info requests. If another
        handler is registered, this one will defer and not run.
        """
        if not forwarded and self.xmpp.event_handled('disco_info_request'):
            return

        node_name = iq['disco_info']['node']
        if not node_name:
            node_name = 'main'

        log.debug("Using default handler for disco#info on node '%s'." % node_name)

        if node_name in self.nodes:
            node = self.nodes[node_name]
            iq.reply().setPayload(node.info.xml).send()
        else:
            log.debug("Node %s requested, but does not exist." % node_name)
            iq.reply().error().setPayload(iq['disco_info'].xml)
            iq['error']['code'] = '404'
            iq['error']['type'] = 'cancel'
            iq['error']['condition'] = 'item-not-found'
            iq.send()

    def handle_disco_items(self, iq, forwarded=False):
        """
        A default handler for disco#items requests. If another
        handler is registered, this one will defer and not run.

        If this handler is called by your own custom handler with
        forwarded set to True, then it will run as normal.
        """
        if not forwarded and self.xmpp.event_handled('disco_items_request'):
            return

        node_name = iq['disco_items']['node']
        if not node_name:
            node_name = 'main'

        log.debug("Using default handler for disco#items on node '%s'." % node_name)

        if node_name in self.nodes:
            node = self.nodes[node_name]
            iq.reply().setPayload(node.items.xml).send()
        else:
            log.debug("Node %s requested, but does not exist." % node_name)
            iq.reply().error().setPayload(iq['disco_items'].xml)
            iq['error']['code'] = '404'
            iq['error']['type'] = 'cancel'
            iq['error']['condition'] = 'item-not-found'
            iq.send()

    # Older interface methods for backwards compatibility

    def getInfo(self, jid, node='', dfrom=None):
        iq = self.xmpp.Iq()
        iq['type'] = 'get'
        iq['to'] = jid
        iq['from'] = dfrom
        iq['disco_info']['node'] = node
        return iq.send()

    def getItems(self, jid, node='', dfrom=None):
        iq = self.xmpp.Iq()
        iq['type'] = 'get'
        iq['to'] = jid
        iq['from'] = dfrom
        iq['disco_items']['node'] = node
        return iq.send()

    def add_feature(self, feature, node='main'):
        self.add_node(node)
        self.nodes[node].addFeature(feature)

    def add_identity(self, category='', itype='', name='', node='main'):
        self.add_node(node)
        self.nodes[node].addIdentity(category=category,
                         id_type=itype,
                         name=name)

    def add_item(self, jid=None, name='', node='main', subnode=''):
        self.add_node(node)
        self.add_node(subnode)
        if jid is None:
            jid = self.xmpp.fulljid
        self.nodes[node].addItem(jid=jid, name=name, node=subnode)
