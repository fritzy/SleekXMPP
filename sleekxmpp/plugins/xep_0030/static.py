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
from sleekxmpp.plugins.xep_0030 import DiscoInfo, DiscoItems


log = logging.getLogger(__name__)


class StaticDisco(object):

    """
    While components will likely require fully dynamic handling
    of service discovery information, most clients and simple bots
    only need to manage a few disco nodes that will remain mostly
    static.

    StaticDisco provides a set of node handlers that will store
    static sets of disco info and items in memory.
    """

    def __init__(self, xmpp):
        """
        Create a static disco interface. Sets of disco#info and
        disco#items are maintained for every given JID and node
        combination. These stanzas are used to store disco
        information in memory without any additional processing.

        Arguments:
            xmpp -- The main SleekXMPP object.
        """
        self.nodes = {}
        self.xmpp = xmpp

    def add_node(self, jid=None, node=None):
        if jid is None:
            jid = self.xmpp.boundjid.full
        if node is None:
            node = ''
        if (jid, node) not in self.nodes:
            self.nodes[(jid, node)] = {'info': DiscoInfo(),
                                       'items': DiscoItems()}
            self.nodes[(jid, node)]['info']['node'] = node
            self.nodes[(jid, node)]['items']['node'] = node

    def get_info(self, jid, node, data):
        if (jid, node) not in self.nodes:
            if not node:
                return DiscoInfo()
            else:
                raise XMPPError(condition='item-not-found')
        else:
            return self.nodes[(jid, node)]['info']

    def del_info(self, jid, node, data):
        if (jid, node) in self.nodes:
            self.nodes[(jid, node)]['info'] = DiscoInfo()

    def get_items(self, jid, node, data):
        if (jid, node) not in self.nodes:
            if not node:
                return DiscoInfo()
            else:
                raise XMPPError(condition='item-not-found')
        else:
            return self.nodes[(jid, node)]['items']

    def set_items(self, jid, node, data):
        items = data.get('items', set())
        self.add_node(jid, node)
        self.nodes[(jid, node)]['items']['items'] = items

    def del_items(self, jid, node, data):
        if (jid, node) in self.nodes:
            self.nodes[(jid, node)]['items'] = DiscoItems()

    def add_identity(self, jid, node, data):
        self.add_node(jid, node)
        self.nodes[(jid, node)]['info'].add_identity(
                data.get('category', ''),
                data.get('itype', ''),
                data.get('name', None),
                data.get('lang', None))

    def set_identities(self, jid, node, data):
        identities = data.get('identities', set())
        self.add_node(jid, node)
        self.nodes[(jid, node)]['info']['identities'] = identities

    def del_identity(self, jid, node, data):
        if (jid, node) not in self.nodes:
            return
        self.nodes[(jid, node)]['info'].del_identity(
                data.get('category', ''),
                data.get('itype', ''),
                data.get('name', None),
                data.get('lang', None))

    def add_feature(self, jid, node, data):
        self.add_node(jid, node)
        self.nodes[(jid, node)]['info'].add_feature(data.get('feature', ''))

    def set_features(self, jid, node, data):
        features = data.get('features', set())
        self.add_node(jid, node)
        self.nodes[(jid, node)]['info']['features'] = features

    def del_feature(self, jid, node, data):
        if (jid, node) not in self.nodes:
            return
        self.nodes[(jid, node)]['info'].del_feature(data.get('feature', ''))

    def add_item(self, jid, node, data):
        self.add_node(jid, node)
        self.nodes[(jid, node)]['items'].add_item(
                data.get('ijid', ''),
                node=data.get('inode', None),
                name=data.get('name', None))

    def del_item(self, jid, node, data):
        if (jid, node) in self.nodes:
            self.nodes[(jid, node)]['items'].del_item(
                    data.get('ijid', ''),
                    node=data.get('inode', None))
