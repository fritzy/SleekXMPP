"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.jid import JID
from sleekxmpp.xmlstream import ElementBase, register_stanza_plugin
from sleekxmpp.plugins import xep_0082


class MUC(ElementBase):
    name = 'x'
    namespace = 'http://jabber.org/protocol/muc'
    plugin_attrib = 'muc_join'
    interfaces = set(['password'])
    sub_interfaces = set(['password'])


class History(ElementBase):
    name = 'history'
    namespace = 'http://jabber.org/protocol/muc'
    plugin_attrib = 'history'
    interfaces = set(['maxchars', 'maxstanzas', 'seconds', 'since'])

    def get_since(self):
        dt = self._get_attr('since')
        if not dt:
            return None
        else:
            return xep_0082.datetime(dt)

    def set_since(self, value):
        self._set_attr('since', str(xep_0082.datetime(value)))


class MUCUser(ElementBase):
    name = 'x'
    namespace = 'http://jabber.org/protocol/muc#user'
    plugin_attrib = 'muc'
    interfaces = set(['password', 'reason', 'affiliation', 'jid', 'nick', 'role'])
    sub_interfaces = set(['password'])

    def get_reason(self):
        return self['item']['reason']

    def set_reason(self, value):
        self['item']['reason'] = value

    def del_reason(self):
        del self['item']['reason']

    def get_affiliation(self):
        return self['item']['affiliation']

    def set_affiliation(self, value):
        self['item']['affiliation'] = value

    def del_affiliation(self):
        del self['item']['affiliation']

    def get_jid(self):
        return self['item']['jid']

    def set_jid(self, value):
        self['item']['jid'] = value

    def del_jid(self):
        del self['item']['jid']

    def get_nick(self):
        return self['item']['nick']

    def set_nick(self, value):
        self['item']['nick'] = value

    def del_nick(self):
        del self['item']['nick']

    def get_role(self):
        return self['item']['role']

    def set_role(self, value):
        self['item']['role'] = value

    def del_role(self):
        del self['item']['role']


class UserDecline(ElementBase):
    name = 'decine'
    namespace = 'http://jabber.org/protocol/muc#user'
    plugin_attrib = 'decline'
    interfaces = set(['to', 'from', 'reason'])
    sub_interfaces = set(['reason'])

    def get_to(self):
        return JID(self._get_attr('to'))

    def set_to(self, value):
        return self._set_attr('to', str(value))

    def get_from(self):
        return JID(self._get_attr('from'))

    def set_from(self, value):
        return self._set_attr('from', str(value))


class UserInvite(ElementBase):
    name = 'invite'
    namespace = 'http://jabber.org/protocol/muc#user'
    plugin_attrib = 'invite'
    plugin_multi_attrib = 'invites'
    interfaces = set(['to', 'from', 'reason'])
    sub_interfaces = set(['reason'])

    def get_to(self):
        return JID(self._get_attr('to'))

    def set_to(self, value):
        return self._set_attr('to', str(value))

    def get_from(self):
        return JID(self._get_attr('from'))

    def set_from(self, value):
        return self._set_attr('from', str(value))


class UserDestroy(ElementBase):
    name = 'destroy'
    namespace = 'http://jabber.org/protocol/muc#user'
    plugin_attrib = 'destroy'
    interfaces = set(['jid', 'reason'])
    sub_interfaces = set(['reason'])

    def get_jid(self):
        return JID(self._get_attr('jid'))

    def set_jid(self, value):
        return self._set_attr('jid', str(value))


class UserItem(ElementBase):
    name = 'item'
    namespace = 'http://jabber.org/protocol/muc#user'
    plugin_attrib = 'item'
    plugin_multi_attrib = 'items'
    interfaces = set(['reason', 'affiliation', 'jid', 'nick', 'role'])
    sub_interfaces = set(['reason'])

    def get_jid(self):
        return JID(self._get_attr('jid'))

    def set_jid(self, value):
        return self._set_attr('jid', str(value))


class UserActor(ElementBase):
    name = 'actor'
    namespace = 'http://jabber.org/protocol/muc#user'
    plugin_attrib = 'actor'
    interfaces = set(['jid', 'nick'])

    def get_jid(self):
        return JID(self._get_attr('jid'))

    def set_jid(self, value):
        return self._set_attr('jid', str(value))


class UserContinue(ElementBase):
    name = 'continue'
    namespace = 'http://jabber.org/protocol/muc#user'
    plugin_attrib = 'continue'
    interfaces = set(['thread'])


class UserStatus(ElementBase):
    name = 'status'
    namespace = 'http://jabber.org/protocol/muc#user'
    plugin_attrib = 'status'
    plugin_multi_attrib = 'statuses'
    interfaces = set(['code'])


class MUCAdmin(ElementBase):
    name = 'query'
    namespace = 'http://jabber.org/protocol/muc#admin'
    plugin_attrib = 'muc_admin'
    interfaces = set()


class AdminItem(UserItem):
    name = 'item'
    namespace = 'http://jabber.org/protocol/muc#admin'
    plugin_attrib = 'item'
    plugin_multi_attrib = 'items'
    interfaces = set(['reason', 'affiliation', 'jid', 'nick', 'role'])
    sub_interfaces = set(['reason'])

    def get_jid(self):
        return JID(self._get_attr('jid'))

    def set_jid(self, value):
        return self._set_attr('jid', str(value))


class AdminActor(ElementBase):
    name = 'actor'
    namespace = 'http://jabber.org/protocol/muc#admin'
    plugin_attrib = 'actor'
    interfaces = set(['jid', 'nick'])

    def get_jid(self):
        return JID(self._get_attr('jid'))

    def set_jid(self, value):
        return self._set_attr('jid', str(value))


class MUCOwner(ElementBase):
    name = 'query'
    namespace = 'http://jabber.org/protocol/muc#owner'
    plugin_attrib = 'muc_owner'
    interfaces = set()


class OwnerDestroy(ElementBase):
    name = 'destroy'
    namespace = 'http://jabber.org/protocol/muc#owner'
    plugin_attrib = 'destroy'
    interfaces = set(['jid', 'reason'])
    sub_interfaces = set(['reason'])

    def get_jid(self):
        return JID(self._get_attr('jid'))

    def set_jid(self, value):
        return self._set_attr('jid', str(value))


register_stanza_plugin(MUC, History)
register_stanza_plugin(MUCUser, UserDecline)
register_stanza_plugin(MUCUser, UserDestroy)
register_stanza_plugin(MUCUser, UserInvite, iterable=True)
register_stanza_plugin(MUCUser, UserItem, iterable=True)
register_stanza_plugin(MUCUser, UserStatus, iterable=True)
register_stanza_plugin(UserItem, UserActor)
register_stanza_plugin(UserItem, UserContinue)
register_stanza_plugin(MUCAdmin, AdminItem, iterable=True)
register_stanza_plugin(AdminItem, AdminActor)
register_stanza_plugin(MUCOwner, OwnerDestroy)
