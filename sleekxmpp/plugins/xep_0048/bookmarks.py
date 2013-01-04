"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp import Iq
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.exceptions import XMPPError
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins.xep_0048 import stanza, Bookmarks, Conference, URL


log = logging.getLogger(__name__)


class XEP_0048(BasePlugin):

    name = 'xep_0048'
    description = 'XEP-0048: Bookmarks'
    dependencies = set(['xep_0045', 'xep_0049', 'xep_0060', 'xep_0163', 'xep_0223'])
    stanza = stanza
    default_config = {
        'auto_join': False,
        'storage_method': 'xep_0049'
    }

    def plugin_init(self):
        register_stanza_plugin(self.xmpp['xep_0060'].stanza.Item, Bookmarks)

        self.xmpp['xep_0049'].register(Bookmarks)
        self.xmpp['xep_0163'].register_pep('bookmarks', Bookmarks)

        self.xmpp.add_event_handler('session_start', self._autojoin)

    def plugin_end(self):
        self.xmpp.del_event_handler('session_start', self._autojoin)

    def _autojoin(self, __):
        if not self.auto_join:
            return

        try:
            result = self.get_bookmarks(method=self.storage_method)
        except XMPPError:
            return

        if self.storage_method == 'xep_0223':
            bookmarks = result['pubsub']['items']['item']['bookmarks']
        else:
            bookmarks = result['private']['bookmarks']

        for conf in bookmarks['conferences']:
            if conf['autojoin']:
                log.debug('Auto joining %s as %s', conf['jid'], conf['nick'])
                self.xmpp['xep_0045'].joinMUC(conf['jid'], conf['nick'],
                        password=conf['password'])

    def set_bookmarks(self, bookmarks, method=None, **iqargs):
        if not method:
            method = self.storage_method
        return self.xmpp[method].store(bookmarks, **iqargs)

    def get_bookmarks(self, method=None, **iqargs):
        if not method:
            method = self.storage_method

        loc = 'storage:bookmarks' if method == 'xep_0223' else 'bookmarks'

        return self.xmpp[method].retrieve(loc, **iqargs)
