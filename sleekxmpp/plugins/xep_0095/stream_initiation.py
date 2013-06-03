"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging
import threading

from uuid import uuid4

from sleekxmpp import Iq, Message
from sleekxmpp.exceptions import XMPPError
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.xmlstream import register_stanza_plugin, JID
from sleekxmpp.plugins.xep_0095 import stanza, SI


log = logging.getLogger(__name__)


SOCKS5 = 'http://jabber.org/protocol/bytestreams'
IBB = 'http://jabber.org/protocol/ibb'


class XEP_0095(BasePlugin):

    name = 'xep_0095'
    description = 'XEP-0095: Stream Initiation'
    dependencies = set(['xep_0020', 'xep_0030', 'xep_0047', 'xep_0065'])
    stanza = stanza

    def plugin_init(self):
        self._profiles = {}
        self._methods = {}
        self._methods_order = []
        self._pending_lock = threading.Lock()
        self._pending= {}

        self.register_method(SOCKS5, 'xep_0065', 100)
        self.register_method(IBB, 'xep_0047', 50)

        register_stanza_plugin(Iq, SI)
        register_stanza_plugin(SI, self.xmpp['xep_0020'].stanza.FeatureNegotiation)

        self.xmpp.register_handler(
            Callback('SI Request',
                StanzaPath('iq@type=set/si'),
                self._handle_request))

        self.api.register(self._add_pending, 'add_pending', default=True)
        self.api.register(self._get_pending, 'get_pending', default=True)
        self.api.register(self._del_pending, 'del_pending', default=True)

    def session_bind(self, jid):
        self.xmpp['xep_0030'].add_feature(SI.namespace)

    def plugin_end(self):
        self.xmpp.remove_handler('SI Request')
        self.xmpp['xep_0030'].del_feature(feature=SI.namespace)

    def register_profile(self, profile_name, plugin):
        self._profiles[profile_name] = plugin

    def unregister_profile(self, profile_name):
        try:
            del self._profiles[profile_name]
        except KeyError:
            pass

    def register_method(self, method, plugin_name, order=50):
        self._methods[method] = (plugin_name, order)
        self._methods_order.append((order, method, plugin_name))
        self._methods_order.sort()

    def unregister_method(self, method):
        if method in self._methods:
            plugin_name, order = self._methods[method]
            del self._methods[method]
            self._methods_order.remove((order, method, plugin_name))
            self._methods_order.sort()

    def _handle_request(self, iq):
        profile = iq['si']['profile']
        sid = iq['si']['id']

        if not sid:
            raise XMPPError(etype='modify', condition='bad-request')
        if profile not in self._profiles:
            raise XMPPError(
                etype='modify',
                condition='bad-request',
                extension='bad-profile',
                extension_ns=SI.namespace)

        neg = iq['si']['feature_neg']['form']['fields']
        options = neg['stream-method']['options'] or []
        methods = []
        for opt in options:
            methods.append(opt['value'])
        for method in methods:
            if method in self._methods:
                supported = True
                break
        else:
            raise XMPPError('bad-request',
                    extension='no-valid-streams',
                    extension_ns=SI.namespace)

        selected_method = None
        log.debug('Available: %s', methods)
        for order, method, plugin in self._methods_order:
            log.debug('Testing: %s', method)
            if method in methods:
                selected_method = method
                break

        receiver = iq['to']
        sender = iq['from']

        self.api['add_pending'](receiver, sid, sender, {
            'response_id': iq['id'],
            'method': selected_method,
            'profile': profile
        })
        self.xmpp.event('si_request', iq)

    def offer(self, jid, sid=None, mime_type=None, profile=None,
                    methods=None, payload=None, ifrom=None,
                    **iqargs):
        if sid is None:
            sid = uuid4().hex
        if methods is None:
            methods = list(self._methods.keys())
        if not isinstance(methods, (list, tuple, set)):
            methods = [methods]

        si = self.xmpp.Iq()
        si['to'] = jid
        si['from'] = ifrom
        si['type'] = 'set'
        si['si']['id'] = sid
        si['si']['mime_type'] = mime_type
        si['si']['profile'] = profile
        if not isinstance(payload, (list, tuple, set)):
            payload = [payload]
        for item in payload:
            si['si'].append(item)
        si['si']['feature_neg']['form'].add_field(
                var='stream-method',
                ftype='list-single',
                options=methods)
        return si.send(**iqargs)

    def accept(self, jid, sid, payload=None, ifrom=None, stream_handler=None):
        stream = self.api['get_pending'](ifrom, sid, jid)
        iq = self.xmpp.Iq()
        iq['id'] = stream['response_id']
        iq['to'] = jid
        iq['from'] = ifrom
        iq['type'] = 'result'
        if payload:
            iq['si'].append(payload)
        iq['si']['feature_neg']['form']['type'] = 'submit'
        iq['si']['feature_neg']['form'].add_field(
                var='stream-method',
                ftype='list-single',
                value=stream['method'])

        if ifrom is None:
            ifrom = self.xmpp.boundjid

        method_plugin = self._methods[stream['method']][0]
        self.xmpp[method_plugin].api['preauthorize_sid'](ifrom, sid, jid)

        self.api['del_pending'](ifrom, sid, jid)

        if stream_handler:
            self.xmpp.add_event_handler('stream:%s:%s' % (sid, jid),
                    stream_handler,
                    threaded=True,
                    disposable=True)
        return iq.send()

    def decline(self, jid, sid, ifrom=None):
        stream = self.api['get_pending'](ifrom, sid, jid)
        if not stream:
            return
        iq = self.xmpp.Iq()
        iq['id'] = stream['response_id']
        iq['to'] = jid
        iq['from'] = ifrom
        iq['type'] = 'error'
        iq['error']['condition'] = 'forbidden'
        iq['error']['text'] = 'Offer declined'
        self.api['del_pending'](ifrom, sid, jid)
        return iq.send()

    def _add_pending(self, jid, node, ifrom, data):
        with self._pending_lock:
            self._pending[(jid, node, ifrom)] = data

    def _get_pending(self, jid, node, ifrom, data):
        with self._pending_lock:
            return self._pending.get((jid, node, ifrom), None)

    def _del_pending(self, jid, node, ifrom, data):
        with self._pending_lock:
            if (jid, node, ifrom) in self._pending:
                del self._pending[(jid, node, ifrom)]
