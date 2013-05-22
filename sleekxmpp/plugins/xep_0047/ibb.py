import uuid
import logging
import threading

from sleekxmpp import Message, Iq
from sleekxmpp.exceptions import XMPPError
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.plugins.xep_0047 import stanza, Open, Close, Data, IBBytestream


log = logging.getLogger(__name__)


class XEP_0047(BasePlugin):

    name = 'xep_0047'
    description = 'XEP-0047: In-band Bytestreams'
    dependencies = set(['xep_0030'])
    stanza = stanza
    default_config = {
        'block_size': 4096,
        'max_block_size': 8192,
        'window_size': 1,
        'auto_accept': False,
    }

    def plugin_init(self):
        self._streams = {}
        self._pending_streams = {}
        self._pending_lock = threading.Lock()
        self._stream_lock = threading.Lock()

        self._preauthed_sids_lock = threading.Lock()
        self._preauthed_sids = {}

        register_stanza_plugin(Iq, Open)
        register_stanza_plugin(Iq, Close)
        register_stanza_plugin(Iq, Data)
        register_stanza_plugin(Message, Data)

        self.xmpp.register_handler(Callback(
            'IBB Open',
            StanzaPath('iq@type=set/ibb_open'),
            self._handle_open_request))

        self.xmpp.register_handler(Callback(
            'IBB Close',
            StanzaPath('iq@type=set/ibb_close'),
            self._handle_close))

        self.xmpp.register_handler(Callback(
            'IBB Data',
            StanzaPath('iq@type=set/ibb_data'),
            self._handle_data))

        self.xmpp.register_handler(Callback(
            'IBB Message Data',
            StanzaPath('message/ibb_data'),
            self._handle_data))

        self.api.register(self._authorized, 'authorized', default=True)
        self.api.register(self._authorized_sid, 'authorized_sid', default=True)
        self.api.register(self._preauthorize_sid, 'preauthorize_sid', default=True)
        self.api.register(self._get_stream, 'get_stream', default=True)
        self.api.register(self._set_stream, 'set_stream', default=True)
        self.api.register(self._del_stream, 'del_stream', default=True)

    def plugin_end(self):
        self.xmpp.remove_handler('IBB Open')
        self.xmpp.remove_handler('IBB Close')
        self.xmpp.remove_handler('IBB Data')
        self.xmpp.remove_handler('IBB Message Data')
        self.xmpp['xep_0030'].del_feature(feature='http://jabber.org/protocol/ibb')

    def session_bind(self, jid):
        self.xmpp['xep_0030'].add_feature('http://jabber.org/protocol/ibb')

    def _get_stream(self, jid, sid, peer_jid, data):
        return self._streams.get((jid, sid, peer_jid), None)

    def _set_stream(self, jid, sid, peer_jid, stream):
        self._streams[(jid, sid, peer_jid)] = stream

    def _del_stream(self, jid, sid, peer_jid, data):
        with self._stream_lock:
            if (jid, sid, peer_jid) in self._streams:
                del self._streams[(jid, sid, peer_jid)]

    def _accept_stream(self, iq):
        receiver = iq['to']
        sender = iq['from']
        sid = iq['ibb_open']['sid']

        if self.api['authorized_sid'](receiver, sid, sender, iq):
            return True
        return self.api['authorized'](receiver, sid, sender, iq)

    def _authorized(self, jid, sid, ifrom, iq):
        if self.auto_accept:
            if iq['ibb_open']['block_size'] <= self.max_block_size:
                return True
        return False

    def _authorized_sid(self, jid, sid, ifrom, iq):
        with self._preauthed_sids_lock:
            if (jid, sid, ifrom) in self._preauthed_sids:
                del self._preauthed_sids[(jid, sid, ifrom)]
                return True
            return False

    def _preauthorize_sid(self, jid, sid, ifrom, data):
        with self._preauthed_sids_lock:
            self._preauthed_sids[(jid, sid, ifrom)] = True

    def open_stream(self, jid, block_size=None, sid=None, window=1, use_messages=False,
                    ifrom=None, block=True, timeout=None, callback=None):
        if sid is None:
            sid = str(uuid.uuid4())
        if block_size is None:
            block_size = self.block_size

        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['to'] = jid
        iq['from'] = ifrom
        iq['ibb_open']['block_size'] = block_size
        iq['ibb_open']['sid'] = sid
        iq['ibb_open']['stanza'] = 'iq'

        stream = IBBytestream(self.xmpp, sid, block_size,
                              iq['from'], iq['to'], window,
                              use_messages)

        with self._stream_lock:
            self._pending_streams[iq['id']] = stream

        self._pending_streams[iq['id']] = stream

        if block:
            resp = iq.send(timeout=timeout)
            self._handle_opened_stream(resp)
            return stream
        else:
            cb = None
            if callback is not None:
                def chained(resp):
                    self._handle_opened_stream(resp)
                    callback(resp)
                cb = chained
            else:
                cb = self._handle_opened_stream
            return iq.send(block=block, timeout=timeout, callback=cb)

    def _handle_opened_stream(self, iq):
        if iq['type'] == 'result':
            with self._stream_lock:
                stream = self._pending_streams.get(iq['id'], None)
            if stream is not None:
                log.debug('IBB stream (%s) accepted by %s', stream.sid, iq['from'])
                stream.self_jid = iq['to']
                stream.peer_jid = iq['from']
                stream.stream_started.set()
                self.api['set_stream'](stream.self_jid, stream.sid, stream.peer_jid, stream)
                self.xmpp.event('ibb_stream_start', stream)
                self.xmpp.event('stream:%s:%s' % (stream.sid, stream.peer_jid), stream)

        with self._stream_lock:
            if iq['id'] in self._pending_streams:
                del self._pending_streams[iq['id']]

    def _handle_open_request(self, iq):
        sid = iq['ibb_open']['sid']
        size = iq['ibb_open']['block_size'] or self.block_size

        log.debug('Received IBB stream request from %s', iq['from'])

        if not sid:
            raise XMPPError(etype='modify', condition='bad-request')

        if not self._accept_stream(iq):
            raise XMPPError(etype='modify', condition='not-acceptable')

        if size > self.max_block_size:
            raise XMPPError('resource-constraint')

        stream = IBBytestream(self.xmpp, sid, size,
                              iq['to'], iq['from'],
                              self.window_size)
        stream.stream_started.set()
        self.api['set_stream'](stream.self_jid, stream.sid, stream.peer_jid, stream)
        iq.reply()
        iq.send()

        self.xmpp.event('ibb_stream_start', stream)
        self.xmpp.event('stream:%s:%s' % (sid, stream.peer_jid), stream)

    def _handle_data(self, stanza):
        sid = stanza['ibb_data']['sid']
        stream = self.api['get_stream'](stanza['to'], sid, stanza['from'])
        if stream is not None and stanza['from'] == stream.peer_jid:
            stream._recv_data(stanza)
        else:
            raise XMPPError('item-not-found')

    def _handle_close(self, iq):
        sid = iq['ibb_close']['sid']
        stream = self.api['get_stream'](iq['to'], sid, iq['from'])
        if stream is not None and iq['from'] == stream.peer_jid:
            stream._closed(iq)
            self.api['del_stream'](stream.self_jid, stream.sid, stream.peer_jid)
        else:
            raise XMPPError('item-not-found')
