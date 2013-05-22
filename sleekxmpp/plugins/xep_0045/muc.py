"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Erik Reuterborg Larsson
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.exceptions import XMPPError
from sleekxmpp.util import Queue, QueueEmpty
from sleekxmpp.stanza import Presence, Message, Iq
from sleekxmpp.plugins.base import BasePlugin
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.xmlstream.handler import Callback, Waiter
from sleekxmpp.xmlstream.matcher import StanzaPath, MatchXMLMask
from sleekxmpp.plugins.xep_0045 import stanza


log = logging.getLogger(__name__)


class MUCJoinTimeout(XMPPError):
    def __init__(self, pres):
        super(MUCJoinTimeout, self).__init__(
                condition='remote-server-timeout',
                etype='cancel')
        self.pres = pres


class MUCJoinError(XMPPError):
    def __init__(self, pres):
        super(MUCJoinError, self).__init__(
                condition=pres['error']['condition'],
                text=pres['error']['text'],
                etype=pres['error']['type'])
        self.pres = pres


class XEP_0045(BasePlugin):

    """
    XEP-0045: Multi-User Chat
    """

    name = 'xep_0045'
    description = 'XEP-0045: Multi-User Chat'
    dependencies = set(['xep_0004', 'xep_0030', 'xep_0203', 'xep_0082', 'xep_0249'])
    stanza = stanza
    default_config = {
        'expose_joined_rooms': False,
    }

    def plugin_init(self):
        register_stanza_plugin(Presence, stanza.MUC)
        register_stanza_plugin(Presence, stanza.MUCUser)
        register_stanza_plugin(Iq, stanza.MUCAdmin)
        register_stanza_plugin(Iq, stanza.MUCOwner)

        self.xmpp.register_handler(
            Callback('MUC Presence',
                StanzaPath('presence/muc'),
                self._handle_presence))
        self.xmpp.register_handler(
            Callback('MUC Message',
                StanzaPath('message@type=groupchat/body'),
                self._handle_message))
        self.xmpp.register_handler(
            Callback('MUC Subject',
                StanzaPath('message@type=groupchat/subject'),
                self._handle_subject))

        self.xmpp.add_event_handler('session_end', self._session_end)

        self.api.register(self._set_self_nick, 'set_self_nick', default=True)
        self.api.register(self._get_self_nick, 'get_self_nick', default=True)
        sefl.api.register(self._is_joined_room, 'is_joined_room', default=True)
        sefl.api.register(self._get_joined_rooms, 'get_joined_rooms', default=True)
        sefl.api.register(self._add_joined_room, 'add_joined_room', default=True)
        sefl.api.register(self._del_joined_room, 'del_joined_room', default=True)

        self._nicks = {}
        self._joined_rooms = {}
        self._roster = {}

    def plugin_end(self):
        self.xmpp.remove_handler('MUC Presence')
        self.xmpp.remove_handler('MUC Message')
        self.xmpp.remove_handler('MUC Subject')
        self.xmpp.del_event_handler('session_end', self._session_end)

    def _session_end(self, _):
        self._nicks = {}
        self._joined_rooms = {}
        self._roster = {}

    def _set_self_nick(self, jid, node, ifrom, data):
        self._nicks[(jid, node)] = data

    def _get_self_nick(self, jid, node, ifrom, data):
        return self._nicks.get((jid, node))

    def _is_joined_room(self, jid, node, ifrom, data):
        return node in self._joined_rooms.get(jid, set())

    def _get_joined_rooms(self, jid, node, ifrom, data):
        return self._joined_rooms.get(jid, set())

    def _add_joined_room(self, jid, node, ifrom, data):
        if jid not in self._joined_rooms:
            self._joined_rooms = set()
        self._joined_rooms[jid].add(node)
        self._nicks[(jid, node)] = data
        self._roster[(jid, node)] = {}

    def _del_joined_room(self, jid, node, ifrom, data):
        if jid in self._joined_rooms:
            self._joined_rooms[jid].remove(node)
        del self._nicks[(jid, node)]
        del self._roster[(jid, node)]

    def plugin_end(self):
        self.xmpp['xep_0030'].del_feature(feature='http://jabber.org/protocol/muc')

    def session_bind(self, jid):
        self.xmpp['xep_0030'].add_feature('http://jabber.org/protocol/muc')

    def _handle_presence(self, pres):
        room = pres['from'].bare

        self.xmpp.event('groupchat_presence', pres)
        self.xmpp.event('muc::%s::presence' % room, pres)

        if pres['type'] == 'unavailable' and self.api['is_joined_room'](pres['to'], pres['from']):
            self.api['del_joined_room'](pres['to'], room)
            self.xmpp.event('muc::%s::left' % room, pres)


        room_id = (pres['to'], pres['from'].bare)
        nick = pres['from'].resource
        if room_id not in self._roster:
            self._roster[room_id] = {}
        if pres['type'] != 'unavailable':
            self._roster[room_id][nick] = pres['muc']['item'].values
        elif nick in self._roster[room_id]:
            del self._roster[room_id][nick]

        statuses = pres['muc']['statuses']
        for status in statuses:
            code = status['code']
            if code == '110':
                if pres['type'] == 'available' and not self.api['is_joined_room'](pres['to'], pres['from']):
                    self.xmpp.event('groupchat_joined', pres)
                    self.xmpp.event('muc::%s::joined' % room, pres)
                    self.api['add_joined_room'](pres['to'], room, None, pres['from'].resource)
                    if self.expose_joined_rooms:
                        self.xmpp['xep_0030'].add_item(
                            jid=pres['to'],
                            node='http://jabber.org/protocol/muc#rooms',
                            ijid=room,
                            name=pres['from'].resource)
            elif code == '170':
                self.xmpp.event('groupchat_logging_enabled', pres)
                self.xmpp.event('muc::%s::logging::enabled' % room, pres)
            elif code == '301':
                self.xmpp.event('groupchat_banned', pres)
                self.xmpp.event('muc::%s::left::banned' % room, pres)
            elif code == '303':
                self.xmpp.event('groupchat_nick_changed', pres)
                self.xmpp.event('muc::%s::nick::changed' % room, pres)
            elif code == '307':
                self.xmpp.event('groupchat_kicked', pres)
                self.xmpp.event('muc::%s::left::kicked' % room, pres)
            elif code == '322':
                self.xmpp.event('groupchat_left_nonmember', pres)
                self.xmpp.event('muc::%s::left::nonmember' % room, pres)
            elif code == '332':
                self.xmpp.event('groupchat_left_shutdown', pres)
                self.xmpp.event('muc::%s::left::shutdown' % room, pres)

    def _handle_message(self, msg):
        self.xmpp.event('groupchat_message', msg)
        self.xmpp.event('muc::%s::message' % msg['from'].bare, msg)

    def _handle_subject(self, msg):
        self.xmpp.event('groupchat_subject', msg)
        self.xmpp.event('muc::%s::subject' % msg['from'].bare, msg)

    def get_rooms(self, **discoargs):
        return self.xmpp['xep_0030'].get_items(**discoargs)

    def join(self, room, nick, password=None, maxchars=None, maxstanzas=None,
                   since=None, seconds=None, block=True, timeout=None,
                   **presargs):
        pid = self.xmpp.new_id()
        pres = self.xmpp.make_presence(**presargs)
        pres['id'] = pid
        pres['to'] = '%s/%s' % (room, nick)
        pres['muc_join']['password'] = password
        pres['muc_join']['history']['maxchars'] = maxchars
        pres['muc_join']['history']['maxstanzas'] = maxstanzas
        pres['muc_join']['history']['seconds'] = seconds
        pres['muc_join']['history']['since'] = since

        pfrom = presargs.get('pfrom', self.xmpp.boundjid)

        self.api['add_joined_room'](pfrom, room, None, nick)

        if block:
            waiter = Queue()

        def on_resp(pres):
            if pres['id'] == pid and pres['type'] == 'error':
                self.xmpp.event('groupchat_join_failed', pres)
                self.xmpp.event('muc::%s::joinfailed' % pres['from'].bare, pres)
                if block:
                    waiter.put(('failed', pres))
            elif block:
                waiter.put(('joined', pres))

            self.xmpp.del_event_handler('presence_error', on_resp)
            self.xmpp.del_event_handler('muc::%s::joined' % room, on_resp)

        self.xmpp.add_event_handler('presence_error', on_resp)
        self.xmpp.add_event_handler('muc::%s::joined' % room, on_resp)

        pres.send()
        if not block:
            return

        if timeout is None:
            timeout = self.xmpp.response_timeout
        elapsed_time = 0
        while elapsed_time < timeout and not self.xmpp.stop.is_set():
            joined = None
            try:
                joined, stanza = waiter.get(True, 1)
                if joined == 'failed':
                    raise MUCJoinError(stanza)
                break
            except QueueEmpty:
                elapsed_time += 1
                if elapsed_time >= timeout:
                    log.warning('Timed out waiting to join MUC: %s' % room)
                    raise MUCJoinTimeout(pres)

    def leave(self, room, pfrom=None, pstatus=None):
        pres = self.xmpp.Presence()
        pres['to'] = '%s/%s' % (room, self.api['get_self_nick'](pfrom, room))
        pres['type'] = 'unavailable'
        pres['status'] = status
        pres.send()

        self.api['del_joined_room'](pfrom, room)

        if self.expose_joined_rooms:
            self.xmpp['xep_0030'].del_item(
                    jid=pfrom,
                    node='http://jabber.org/protocol/muc#rooms',
                    ijid=room)

    def get_roster(self, room, pfrom=None):
        roster = self.xmpp.roster[pfrom][room].resources

        if pfrom is None:
            pfrom = self.xmpp.boundjid

        for nick in roster:
            roster[nick]['muc'] = self._roster.get((pfrom, room), {}).get(nick, {})

        return roster

    def set_subject(self, room, subject, mfrom=None):
        msg = self.xmpp.Message()
        msg['to'] = '%s/%s' % (room, self.api['get_self_nick'](pfrom, room))
        msg['type'] = 'groupchat'
        msg._set_sub_text('subject', subject or '', keep=True)
        msg.send()

    def change_nick(self, room, nick, pfrom=None):
        pres = self.xmpp.Presence()
        pres['id'] = self.xmpp.new_id()
        pres['to'] = '%s/%s' % (room, nick)
        pres['from'] = pfrom

        pfrom = pfrom or self.xmpp.boundjid
        self.api['set_self_nick'](pfrom, room, None, nick)

        pres.send()

    def invite(self, room, jid, reason=None, password=None, thread=None,
                     continuation=None, mfrom=None, mediated=False):
        if not mediated:
            self.xmpp['xep_0249'].send_invitation(jid, room,
                    password=password,
                    reason=reason,
                    continuation=continuation,
                    thread=thread,
                    ifrom=mfrom)
        else:
            msg = self.xmpp.Message()
            msg['to'] = to
            msg['from'] = mfrom
            msg['muc']['invite']['to'] = jid
            msg['muc']['invite']['reason'] = reason
            msg['muc']['invite']['password'] = password

            if thread:
                msg['muc']['continue']['thread'] = thread
            elif continuation:
                msg['muc'].enable('continue')
            msg.send()

    def get_room_config(self, room, ifrom=None, **iqargs):
        iq = self.xmpp.Iq()
        iq['type'] = 'get'
        iq['to'] = room
        iq['from'] = ifrom
        iq.enable('muc_owner')
        return iq.send(**iqargs)

    def set_room_config(self, room, config, ifrom=None, **iqargs):
        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['to'] = room
        iq['from'] = ifrom
        iq['muc_owner'].append(config)
        return iq.send(**iqargs)

    def destroy(self, room, reason=None, ifrom=None, **iqargs):
        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['to'] = room
        iq['from'] = ifrom
        iq['muc_owner']['destroy']['reason'] = reason
        return iq.send(**iqargs)

    def kick(self, room, nick, **args):
        return self.set_role(room, nick, 'none', **args)

    def ban(self, room, jid, reason=None, ifrom=None, **iqargs):
        return self.set_affiliation(room, jid, 'outcast', **args)

    def get_users(self, room, role=None, affiliation=None, ifrom=None, **iqargs):
        iq = self.xmpp.Iq()
        iq['type'] = 'get'
        iq['to'] = room
        iq['from'] = ifrom
        iq['muc_admin']['item']['role'] = role
        iq['muc_admin']['item']['affiliation'] = affiliation
        return iq.send(**iqargs)

    def set_affiliation(self, room, jid, affiliation, reason=None, ifrom=None, **iqargs):
        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['to'] = room
        iq['from'] = ifrom
        iq['muc_admin']['item']['jid'] = jid
        iq['muc_admin']['item']['affiliation'] = affiliation
        iq['muc_admin']['item']['reason'] = reason
        return iq.send(**iqargs)

    def set_role(self, room, nick, role, reason=None, ifrom=None, **iqargs):
        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['to'] = room
        iq['from'] = ifrom
        iq['muc_admin']['item']['nick'] = nick
        iq['muc_admin']['item']['role'] = role
        iq['muc_admin']['item']['reason'] = reason
        return iq.send(**iqargs)
