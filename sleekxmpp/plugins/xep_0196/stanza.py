"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ElementBase, ET


class UserGaming(ElementBase):

    name = 'gaming'
    namespace = 'urn:xmpp:gaming:0'
    plugin_attrib = 'gaming'
    interfaces = set(['character_name', 'character_profile', 'name',
                        'level', 'server_address', 'server_name', 'uri'])
    sub_interfaces = interfaces

