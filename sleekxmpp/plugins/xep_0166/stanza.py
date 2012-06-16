"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ElementBase, ET


class Jingle(ElementBase):

    name = 'jingle'
    namespace = 'urn:xmpp:jingle:1'
    plugin_attrib = 'jingle'
    interfaces = set(['action', 'initiator', 'responder', 'sid'])

    actions = set(['content-accept', 'content-add', 'content-modify',
                   'content-reject', 'content-remove', 'description-info',
                   'security-info', 'session-accept', 'session-info',
                   'session-initiate', 'session-terminate', 'transport-accept',
                   'transport-info', 'transport-reject', 'transport-replace'])

    def set_action(self, value):
        if value not in self.actions:
            raise ValueError('Unknown Jingle action: %s.' % value)
        self._set_attr('action', value)
