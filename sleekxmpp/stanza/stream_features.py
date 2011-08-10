"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ElementBase, StanzaBase, ET
from sleekxmpp.xmlstream import register_stanza_plugin


class StreamFeatures(StanzaBase):

    """
    """

    name = 'features'
    namespace = 'http://etherx.jabber.org/streams'
    interfaces = set(('features', 'required', 'optional'))
    sub_interfaces = interfaces
    plugin_tag_map = {}
    plugin_attrib_map = {}

    def setup(self, xml):
        StanzaBase.setup(self, xml)
        self.values = self.values

    def get_features(self):
        """
        """
        return self.plugins

    def set_features(self, value):
        """
        """
        pass

    def del_features(self):
        """
        """
        pass

    def get_required(self):
        """
        """
        features = self['features']
        return [f for n, f in features.items() if f['required']]

    def get_optional(self):
        """
        """
        features = self['features']
        return [f for n, f in features.items() if not f['required']]
