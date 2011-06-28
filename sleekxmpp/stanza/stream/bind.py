"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import Iq
from sleekxmpp.stanza.stream import StreamFeatures
from sleekxmpp.xmlstream import ElementBase, ET, register_stanza_plugin


class Bind(ElementBase):

    """
    """

    name = 'bind'
    namespace = 'urn:ietf:params:xml:ns:xmpp-bind'
    interfaces = set(('resource', 'jid'))
    sub_interfaces = interfaces
    plugin_attrib = 'bind'


register_stanza_plugin(Iq, Bind)
register_stanza_plugin(StreamFeatures, Bind)
