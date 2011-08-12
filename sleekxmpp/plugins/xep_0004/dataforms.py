"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import copy

from sleekxmpp.thirdparty import OrderedDict

from sleekxmpp import Message
from sleekxmpp.xmlstream import register_stanza_plugin, ElementBase, ET
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.plugins.xep_0004 import stanza
from sleekxmpp.plugins.xep_0004.stanza import Form, FormField, FieldOption


class xep_0004(base_plugin):
    """
    XEP-0004: Data Forms
    """

    def plugin_init(self):
        self.xep = '0004'
        self.description = 'Data Forms'
        self.stanza = stanza

        self.xmpp.registerHandler(
            Callback('Data Form',
                 StanzaPath('message/form'),
                 self.handle_form))

        register_stanza_plugin(FormField, FieldOption, iterable=True)
        register_stanza_plugin(Form, FormField, iterable=True)
        register_stanza_plugin(Message, Form)

    def make_form(self, ftype='form', title='', instructions=''):
        f = Form()
        f['type'] = ftype
        f['title'] = title
        f['instructions'] = instructions
        return f

    def post_init(self):
        base_plugin.post_init(self)
        self.xmpp.plugin['xep_0030'].add_feature('jabber:x:data')

    def handle_form(self, message):
        self.xmpp.event("message_xform", message)

    def build_form(self, xml):
        return Form(xml=xml)


xep_0004.makeForm = xep_0004.make_form
xep_0004.buildForm = xep_0004.build_form
