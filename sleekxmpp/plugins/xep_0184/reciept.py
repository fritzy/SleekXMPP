"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012 Erik Reuterborg Larsson, Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import Message
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.plugins.xep_0184 import stanza, Request, Received


class xep_0184(base_plugin):
    """
    XEP-0184: Message Delivery Receipts
    """

    def plugin_init(self):
        self.xep = '0184'
        self.description = 'Message Delivery Receipts'
        self.stanza = stanza

        register_stanza_plugin(Message, Request)
        register_stanza_plugin(Message, Received)

    def post_init(self):
        base_plugin.post_init(self)
        self.xmpp.plugin['xep_0030'].add_feature('urn:xmpp:receipts')

    def ack(self, message):
        """
        Acknowledges a message

        Arguments:
            message -- The message to acknowledge.
        """
        mto = message['to']
        mfrom = message['from']
        mid = message['id']
        msg = self.xmpp.make_message(mto=mfrom, mfrom=mto)
        msg['reciept_received']['id'] = mid
        msg['id'] = self.xmpp.new_id()
        msg.send()
