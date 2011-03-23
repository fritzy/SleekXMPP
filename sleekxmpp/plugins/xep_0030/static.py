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

    Attributes:
        nodes -- A dictionary mapping (JID, node) tuples to a dict
                 containing a disco#info and a disco#items stanza.
        xmpp  -- The main SleekXMPP object.
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
        """
        Create a new set of stanzas for the provided
        JID and node combination.

        Arguments:
            jid  -- The JID that will own the new stanzas.
            node -- The node that will own the new stanzas.
        """
        if jid is None:
            jid = self.xmpp.boundjid.full
        if node is None:
            node = ''
        if (jid, node) not in self.nodes:
            self.nodes[(jid, node)] = {'info': DiscoInfo(),
                                       'items': DiscoItems()}
            self.nodes[(jid, node)]['info']['node'] = node
            self.nodes[(jid, node)]['items']['node'] = node

    # =================================================================
    # Node Handlers
    #
    # Each handler accepts three arguments: jid, node, and data.
    # The jid and node parameters together determine the set of
    # info and items stanzas that will be retrieved or added.
    # The data parameter is a dictionary with additional paramters
    # that will be passed to other calls.

    def get_info(self, jid, node, data):
        """
        Return the stored info data for the requested JID/node combination.

        The data parameter is not used.
        """
        if (jid, node) not in self.nodes:
            if not node:
                return DiscoInfo()
            else:
                raise XMPPError(condition='item-not-found')
        else:
            return self.nodes[(jid, node)]['info']

    def del_info(self, jid, node, data):
        """
        Reset the info stanza for a given JID/node combination.

        The data parameter is not used.
        """
        if (jid, node) in self.nodes:
            self.nodes[(jid, node)]['info'] = DiscoInfo()

    def get_items(self, jid, node, data):
        """
        Return the stored items data for the requested JID/node combination.

        The data parameter is not used.
        """
        if (jid, node) not in self.nodes:
            if not node:
                return DiscoInfo()
            else:
                raise XMPPError(condition='item-not-found')
        else:
            return self.nodes[(jid, node)]['items']

    def set_items(self, jid, node, data):
        """
        Replace the stored items data for a JID/node combination.

        The data parameter may provided:
            items -- A set of items in tuple format.
        """
        items = data.get('items', set())
        self.add_node(jid, node)
        self.nodes[(jid, node)]['items']['items'] = items

    def del_items(self, jid, node, data):
        """
        Reset the items stanza for a given JID/node combination.

        The data parameter is not used.
        """
        if (jid, node) in self.nodes:
            self.nodes[(jid, node)]['items'] = DiscoItems()

    def add_identity(self, jid, node, data):
        """
        Add a new identity to te JID/node combination.

        The data parameter may provide:
            category -- The general category to which the agent belongs.
            itype    -- A more specific designation with the category.
            name     -- Optional human readable name for this identity.
            lang     -- Optional standard xml:lang value.
        """
        self.add_node(jid, node)
        self.nodes[(jid, node)]['info'].add_identity(
                data.get('category', ''),
                data.get('itype', ''),
                data.get('name', None),
                data.get('lang', None))

    def set_identities(self, jid, node, data):
        """
        Add or replace all identities for a JID/node combination.

        The data parameter should include:
            identities -- A list of identities in tuple form:
                            (category, type, name, lang)
        """
        identities = data.get('identities', set())
        self.add_node(jid, node)
        self.nodes[(jid, node)]['info']['identities'] = identities

    def del_identity(self, jid, node, data):
        """
        Remove an identity from a JID/node combination.

        The data parameter may provide:
            category -- The general category to which the agent belonged.
            itype    -- A more specific designation with the category.
            name     -- Optional human readable name for this identity.
            lang     -- Optional, standard xml:lang value.
        """
        if (jid, node) not in self.nodes:
            return
        self.nodes[(jid, node)]['info'].del_identity(
                data.get('category', ''),
                data.get('itype', ''),
                data.get('name', None),
                data.get('lang', None))

    def del_identities(self, jid, node, data):
        """
        Remove all identities from a JID/node combination.

        The data parameter is not used.
        """
        if (jid, node) not in self.nodes:
            return
        del self.nodes[(jid, node)]['info']['identities']

    def add_feature(self, jid, node, data):
        """
        Add a feature to a JID/node combination.

        The data parameter should include:
            feature -- The namespace of the supported feature.
        """
        self.add_node(jid, node)
        self.nodes[(jid, node)]['info'].add_feature(data.get('feature', ''))

    def set_features(self, jid, node, data):
        """
        Add or replace all features for a JID/node combination.

        The data parameter should include:
            features -- The new set of supported features.
        """
        features = data.get('features', set())
        self.add_node(jid, node)
        self.nodes[(jid, node)]['info']['features'] = features

    def del_feature(self, jid, node, data):
        """
        Remove a feature from a JID/node combination.

        The data parameter should include:
            feature -- The namespace of the removed feature.
        """
        if (jid, node) not in self.nodes:
            return
        self.nodes[(jid, node)]['info'].del_feature(data.get('feature', ''))

    def del_features(self, jid, node, data):
        """
        Remove all features from a JID/node combination.

        The data parameter is not used.
        """
        if (jid, node) not in self.nodes:
            return
        del self.nodes[(jid, node)]['info']['features']

    def add_item(self, jid, node, data):
        """
        Add an item to a JID/node combination.

        The data parameter may include:
            ijid  -- The JID for the item.
            inode -- Optional additional information to reference
                     non-addressable items.
            name  -- Optional human readable name for the item.
        """
        self.add_node(jid, node)
        self.nodes[(jid, node)]['items'].add_item(
                data.get('ijid', ''),
                node=data.get('inode', ''),
                name=data.get('name', ''))

    def del_item(self, jid, node, data):
        """
        Remove an item from a JID/node combination.

        The data parameter may include:
            ijid  -- JID of the item to remove.
            inode -- Optional extra identifying information.
        """
        if (jid, node) in self.nodes:
            self.nodes[(jid, node)]['items'].del_item(
                    data.get('ijid', ''),
                    node=data.get('inode', None))
