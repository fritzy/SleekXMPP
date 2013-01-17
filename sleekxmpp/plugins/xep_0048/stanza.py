"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ET, ElementBase, register_stanza_plugin


class Bookmarks(ElementBase):
    name = 'storage'
    namespace = 'storage:bookmarks'
    plugin_attrib = 'bookmarks'
    interfaces = set()

    def add_conference(self, jid, nick, name=None, autojoin=None, password=None):
        conf = Conference()
        conf['jid'] = jid
        conf['nick'] = nick
        if name is None:
            name = jid
        conf['name'] = name
        conf['autojoin'] = autojoin
        conf['password'] = password
        self.append(conf)

    def add_url(self, url, name=None):
        saved_url = URL()
        saved_url['url'] = url
        if name is None:
            name = url
        saved_url['name'] = name
        self.append(saved_url)


class Conference(ElementBase):
    name = 'conference'
    namespace = 'storage:bookmarks'
    plugin_attrib = 'conference'
    plugin_multi_attrib = 'conferences'
    interfaces = set(['nick', 'password', 'autojoin', 'jid', 'name'])
    sub_interfaces = set(['nick', 'password'])

    def get_autojoin(self):
        value = self._get_attr('autojoin')
        return value in ('1', 'true')

    def set_autojoin(self, value):
        del self['autojoin']
        if value in ('1', 'true', True):
            self._set_attr('autojoin', 'true')


class URL(ElementBase):
    name = 'url'
    namespace = 'storage:bookmarks'
    plugin_attrib = 'url'
    plugin_multi_attrib = 'urls'
    interfaces = set(['url', 'name'])


register_stanza_plugin(Bookmarks, Conference, iterable=True)
register_stanza_plugin(Bookmarks, URL, iterable=True)
