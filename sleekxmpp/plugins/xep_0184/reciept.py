"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012 Erik Reuterborg Larsson, Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import Message
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.plugins.xep_0184 import stanza, Request, Received


class XEP_0184(BasePlugin):

    """
    XEP-0184: Message Delivery Receipts
    """

    name = 'xep_0184'
    description = 'XEP-0184: Message Delivery Receipts'
    dependencies = set(['xep_0030'])
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Message, Request)
        register_stanza_plugin(Message, Received)

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
