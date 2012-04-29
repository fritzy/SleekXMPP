"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import hashlib
import logging

from sleekxmpp.stanza import Presence
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.plugins.base import BasePlugin
from sleekxmpp.plugins.xep_0153 import stanza, VCardTempUpdate


log = logging.getLogger(__name__)


class XEP_0153(BasePlugin):

    name = 'xep_0153'
    description = 'XEP-0153: vCard-Based Avatars'
    dependencies = set(['xep_0054'])
    stanza = stanza

    def plugin_init(self):
        self._hashes = {}

        register_stanza_plugin(Presence, VCardTempUpdate)

        self.xmpp.add_filter('out', self._update_presence)

        self.xmpp.add_event_handler('session_start', self._start)

        self.xmpp.add_event_handler('presence_available', self._recv_presence)
        self.xmpp.add_event_handler('presence_dnd', self._recv_presence)
        self.xmpp.add_event_handler('presence_xa', self._recv_presence)
        self.xmpp.add_event_handler('presence_chat', self._recv_presence)
        self.xmpp.add_event_handler('presence_away', self._recv_presence)

        self.api.register(self._set_hash, 'set_hash', default=True)
        self.api.register(self._get_hash, 'get_hash', default=True)

    def set_avatar(self, jid=None, avatar=None, mtype=None, block=True, 
                   timeout=None, callback=None):
        vcard = self.xmpp['xep_0054'].get_vcard(jid, cached=True)
        vcard = vcard['vcard_temp']
        vcard['PHOTO']['TYPE'] = mtype
        vcard['PHOTO']['BINVAL'] = avatar
        self.xmpp['xep_0054'].publish_vcard(jid=jid, vcard=vcard)
        self._reset_hash(jid)

    def _start(self, event):
        self.xmpp['xep_0054'].get_vcard()

    def _update_presence(self, stanza):
        if not isinstance(stanza, Presence):
            return stanza

        current_hash = self.api['get_hash'](stanza['from'])
        stanza['vcard_temp_update']['photo'] = current_hash
        return stanza

    def _reset_hash(self, jid=None):
        own_jid = (jid.bare == self.xmpp.boundjid.bare)
        if self.xmpp.is_component:
            own_jid = (jid.domain == self.xmpp.boundjid.domain)
     
        if jid is not None:
            jid = jid.bare
        self.api['set_hash'](jid, args=None)
        if own_jid:
            self.xmpp.roster[jid].send_last_presence()

        iq = self.xmpp['xep_0054'].get_vcard(
                jid=jid, 
                ifrom=self.xmpp.boundjid)
        data = iq['vcard_temp']['PHOTO']['BINVAL']
        if not data:
            new_hash = ''
        else:
            new_hash = hashlib.sha1(data).hexdigest()
        self.api['set_hash'](jid, args=new_hash)
        if own_jid:
            self.xmpp.roster[jid].send_last_presence()

    def _recv_presence(self, pres):
        if not pres.match('presence/vcard_temp_update'):
            self.api['set_hash'](pres['from'], args=None)
            return
        data = pres['vcard_temp_update']['photo']
        if data is None:
            return
        elif data == '' or data != self.api['get_hash'](pres['to']):
            self._reset_hash(pres['from'])

    # =================================================================

    def _get_hash(self, jid, node, ifrom, args):
        return self._hashes.get(jid.bare, None)

    def _set_hash(self, jid, node, ifrom, args):
        self._hashes[jid.bare] = args
