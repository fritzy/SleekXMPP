"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ElementBase, ET, register_stanza_plugin


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
        if not value:
            del self['action']
        elif value not in self.actions:
            raise ValueError('Unknown Jingle action: %s.' % value)
        else:
            self._set_attr('action', value)


class Content(ElementBase):

    name = 'content'
    namespace = 'urn:xmpp:jingle:1'
    plugin_attrib = 'content'
    multi_plugin_attrib = 'content_items'
    interfaces = set(['creator', 'disposition', 'name', 'senders', 
                      'description', 'transport', 'security'])

    senders = set(['initiator', 'none', 'responder', 'both'])

    def _get_section(self, name):
        for _, plugin in self.plugins.items():
            if plugin.name == name:
                return plugin
        return ''

    def _del_section(self, name):
        for _, plugin in self.plugins.items():
            if plugin.name == name:
                del self[plugin.plugin_attrib]

    def _set_section(self, name, value):
        self._del_section(name)
        self.append(value)

    def get_description(self):
        return self._get_section('description')

    def get_transport(self):
        return self._get_section('transport')

    def get_security(self):
        return self._get_section('security')

    def set_description(self, value):
        return self._set_section('description', value)

    def set_transport(self, value):
        return self._set_section('transport', value)

    def set_security(self, value):
        return self._set_section('security', value)

    def del_description(self):
        return self._del_section('description')

    def del_transport(self):
        return self._del_section('transport')

    def del_security(self):
        return self._del_section('security')

    def set_creator(self, value):
        if not value:
            del self['creator']
        elif value not in ('initiator', 'responder'):
            raise ValueError('Unknown Jingle creator: %s' % value)
        else:
            self._set_attr('creator', value)

    def set_senders(self, value):
        if not value:
            del self['senders']
        elif value not in self.senders:
            raise ValueError('Unknown Jingle sender: %s.' % value)
        else:
            self._set_attr('senders', value)

    def get_senders(self):
        return self._get_attr('senders', default='both')


class Reason(ElementBase):

    name = 'reason'
    namespace = 'urn:xmpp:jingle:1'
    plugin_attrib = 'reason'
    interfaces = set(['condition', 'text', 'alternative_session'])
    sub_interfaces = set(['text'])
    conditions = set(['alternative-session', 'busy', 'cancel',
                      'onnectivity-error', 'decline', 'expired',
                      'failed-application', 'general-error', 'gone',
                      'incompatible-parameters', 'media-error',
                      'security-error', 'success', 'timeout',
                      'unsupported_applications', 'unsupported_transports'])

    def get_condition(self):
        for cond in self.conditions:
            if self.xml.find('{%s}%s' % (self.namespace, cond)) is not None:
                return cond
        return ''

    def set_condition(self, value):
        self.del_condition()
        if value:
            cond = ET.Element('{%s}%s' % (self.namespace, value))
            self.xml.append(cond)

    def del_condition(self):
        for name in self.conditions:
             cond = self.xml.find('{%s}%s' % (self.namespace, name))
             if cond is not None:
                 self.xml.remove(cond)

    def get_alternative_session(self):
        return self._get_sub_text('alternative-session/sid', default='')

    def set_alternative_session(self, value):
        self._set_sub_text('alternative-session/sid', value)

    def del_alternative_session(self):
        self._del_sub('alternative-session/sid')


register_stanza_plugin(Jingle, Content, iterable=True)
register_stanza_plugin(Jingle, Reason)
