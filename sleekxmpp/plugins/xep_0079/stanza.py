"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from __future__ import unicode_literals

from sleekxmpp.xmlstream import ElementBase, register_stanza_plugin


class AMP(ElementBase):
    namespace = 'http://jabber.org/protocol/amp'
    name = 'amp'
    plugin_attrib = 'amp'
    interfaces = set(['from', 'to', 'status', 'per_hop'])

    def get_from(self):
        return JID(self._get_attr('from'))

    def set_from(self, value):
        return self._set_attr('from', str(value))

    def get_to(self):
        return JID(self._get_attr('from'))

    def set_to(self, value):
        return self._set_attr('to', str(value))

    def get_per_hop(self):
        return self._get_attr('per-hop') == 'true'

    def set_per_hop(self, value):
        if value:
            return self._set_attr('per-hop', 'true')
        else:
            return self._del_attr('per-hop')

    def del_per_hop(self):
        return self._del_attr('per-hop')

    def add_rule(self, action, condition, value):
        rule = Rule(parent=self)
        rule['action'] = action
        rule['condition'] = condition
        rule['value'] = value


class Rule(ElementBase):
    namespace = 'http://jabber.org/protocol/amp'
    name = 'rule'
    plugin_attrib = name
    plugin_multi_attrib = 'rules'
    interfaces = set(['action', 'condition', 'value'])


class InvalidRules(ElementBase):
    namespace = 'http://jabber.org/protocol/amp'
    name = 'invalid-rules'
    plugin_attrib = 'invalid_rules'


class UnsupportedConditions(ElementBase):
    namespace = 'http://jabber.org/protocol/amp'
    name = 'unsupported-conditions'
    plugin_attrib = 'unsupported_conditions'


class UnsupportedActions(ElementBase):
    namespace = 'http://jabber.org/protocol/amp'
    name = 'unsupported-actions'
    plugin_attrib = 'unsupported_actions'


class FailedRule(Rule):
    namespace = 'http://jabber.org/protocol/amp#errors'


class FailedRules(ElementBase):
    namespace = 'http://jabber.org/protocol/amp#errors'
    name = 'failed-rules'
    plugin_attrib = 'failed_rules'


class AMPFeature(ElementBase):
    namespace = 'http://jabber.org/features/amp'
    name = 'amp'


register_stanza_plugin(AMP, Rule, iterable=True)
register_stanza_plugin(InvalidRules, Rule, iterable=True)
register_stanza_plugin(UnsupportedConditions, Rule, iterable=True)
register_stanza_plugin(UnsupportedActions, Rule, iterable=True)
register_stanza_plugin(FailedRules, FailedRule, iterable=True)
