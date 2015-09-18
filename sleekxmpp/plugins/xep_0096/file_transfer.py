"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp import Iq, Message
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.xmlstream import register_stanza_plugin, JID
from sleekxmpp.plugins.xep_0096 import stanza, File


log = logging.getLogger(__name__)


class XEP_0096(BasePlugin):

    name = 'xep_0096'
    description = 'XEP-0096: SI File Transfer'
    dependencies = set(['xep_0095'])
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(self.xmpp['xep_0095'].stanza.SI, File)

        self.xmpp['xep_0095'].register_profile(File.namespace, self)

    def session_bind(self, jid):
        self.xmpp['xep_0030'].add_feature(File.namespace)

    def plugin_end(self):
        self.xmpp['xep_0030'].del_feature(feature=File.namespace)
        self.xmpp['xep_0095'].unregister_profile(File.namespace, self)

    def request_file_transfer(self, jid, sid=None, name=None, size=None,
                                    desc=None, hash=None, date=None,
                                    allow_ranged=False, mime_type=None,
                                    **iqargs):
        data = File()
        data['name'] = name
        data['size'] = size
        data['date'] = date
        data['desc'] = desc
        data['hash'] = hash
        if allow_ranged:
            data.enable('range')

        return self.xmpp['xep_0095'].offer(jid,
                sid=sid,
                mime_type=mime_type,
                profile=File.namespace,
                payload=data,
                **iqargs)
