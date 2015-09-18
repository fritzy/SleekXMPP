import logging
import threading
import socket

from hashlib import sha1
from uuid import uuid4

from sleekxmpp.thirdparty.socks import socksocket, PROXY_TYPE_SOCKS5

from sleekxmpp.stanza import Iq
from sleekxmpp.exceptions import XMPPError
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.plugins.base import base_plugin

from sleekxmpp.plugins.xep_0065 import stanza, Socks5


log = logging.getLogger(__name__)


class XEP_0065(base_plugin):

    name = 'xep_0065'
    description = "Socks5 Bytestreams"
    dependencies = set(['xep_0030'])
    default_config = {
        'auto_accept': False
    }

    def plugin_init(self):
        register_stanza_plugin(Iq, Socks5)

        self._proxies = {}
        self._sessions = {}
        self._sessions_lock = threading.Lock()

        self._preauthed_sids_lock = threading.Lock()
        self._preauthed_sids = {}

        self.xmpp.register_handler(
            Callback('Socks5 Bytestreams',
                     StanzaPath('iq@type=set/socks/streamhost'),
                     self._handle_streamhost))

        self.api.register(self._authorized, 'authorized', default=True)
        self.api.register(self._authorized_sid, 'authorized_sid', default=True)
        self.api.register(self._preauthorize_sid, 'preauthorize_sid', default=True)

    def session_bind(self, jid):
        self.xmpp['xep_0030'].add_feature(Socks5.namespace)

    def plugin_end(self):
        self.xmpp.remove_handler('Socks5 Bytestreams')
        self.xmpp.remove_handler('Socks5 Streamhost Used')
        self.xmpp['xep_0030'].del_feature(feature=Socks5.namespace)

    def get_socket(self, sid):
        """Returns the socket associated to the SID."""
        return self._sessions.get(sid, None)

    def handshake(self, to, ifrom=None, sid=None, timeout=None):
        """ Starts the handshake to establish the socks5 bytestreams
        connection.
        """
        if not self._proxies:
            self._proxies = self.discover_proxies()

        if sid is None:
            sid = uuid4().hex

        used = self.request_stream(to, sid=sid, ifrom=ifrom, timeout=timeout)
        proxy = used['socks']['streamhost_used']['jid']

        if proxy not in self._proxies:
            log.warning('Received unknown SOCKS5 proxy: %s', proxy)
            return

        with self._sessions_lock:
            self._sessions[sid] = self._connect_proxy(
                    sid,
                    self.xmpp.boundjid,
                    to,
                    self._proxies[proxy][0],
                    self._proxies[proxy][1],
                    peer=to)

        # Request that the proxy activate the session with the target.
        self.activate(proxy, sid, to, timeout=timeout)
        socket = self.get_socket(sid)
        self.xmpp.event('stream:%s:%s' % (sid, to), socket)
        return socket

    def request_stream(self, to, sid=None, ifrom=None, block=True, timeout=None, callback=None):
        if sid is None:
            sid = uuid4().hex

        # Requester initiates S5B negotiation with Target by sending
        # IQ-set that includes the JabberID and network address of
        # StreamHost as well as the StreamID (SID) of the proposed
        # bytestream.
        iq = self.xmpp.Iq()
        iq['to'] = to
        iq['from'] = ifrom
        iq['type'] = 'set'
        iq['socks']['sid'] = sid
        for proxy, (host, port) in self._proxies.items():
            iq['socks'].add_streamhost(proxy, host, port)
        return iq.send(block=block, timeout=timeout, callback=callback)

    def discover_proxies(self, jid=None, ifrom=None, timeout=None):
        """Auto-discover the JIDs of SOCKS5 proxies on an XMPP server."""
        if jid is None:
            if self.xmpp.is_component:
                jid = self.xmpp.server
            else:
                jid = self.xmpp.boundjid.server

        discovered = set()

        disco_items = self.xmpp['xep_0030'].get_items(jid, timeout=timeout)

        for item in disco_items['disco_items']['items']:
            try:
                disco_info = self.xmpp['xep_0030'].get_info(item[0], timeout=timeout)
            except XMPPError:
                continue
            else:
                # Verify that the identity is a bytestream proxy.
                identities = disco_info['disco_info']['identities']
                for identity in identities:
                    if identity[0] == 'proxy' and identity[1] == 'bytestreams':
                        discovered.add(disco_info['from'])

        for jid in discovered:
            try:
                addr = self.get_network_address(jid, ifrom=ifrom, timeout=timeout)
                self._proxies[jid] = (addr['socks']['streamhost']['host'],
                                      addr['socks']['streamhost']['port'])
            except XMPPError:
                continue

        return self._proxies

    def get_network_address(self, proxy, ifrom=None, block=True, timeout=None, callback=None):
        """Get the network information of a proxy."""
        iq = self.xmpp.Iq(sto=proxy, stype='get', sfrom=ifrom)
        iq.enable('socks')
        return iq.send(block=block, timeout=timeout, callback=callback)

    def _handle_streamhost(self, iq):
        """Handle incoming SOCKS5 session request."""
        sid = iq['socks']['sid']
        if not sid:
            raise XMPPError(etype='modify', condition='bad-request')

        if not self._accept_stream(iq):
            raise XMPPError(etype='modify', condition='not-acceptable')

        streamhosts = iq['socks']['streamhosts']
        conn = None
        used_streamhost = None

        sender = iq['from']
        for streamhost in streamhosts:
            try:
                conn = self._connect_proxy(sid,
                    sender,
                    self.xmpp.boundjid,
                    streamhost['host'],
                    streamhost['port'],
                    peer=sender)
                used_streamhost = streamhost['jid']
                break
            except socket.error:
                continue
        else:
            raise XMPPError(etype='cancel', condition='item-not-found')

        iq.reply()
        with self._sessions_lock:
            self._sessions[sid] = conn
        iq['socks']['sid'] = sid
        iq['socks']['streamhost_used']['jid'] = used_streamhost
        iq.send()
        self.xmpp.event('socks5_stream', conn)
        self.xmpp.event('stream:%s:%s' % (sid, conn.peer_jid), conn)

    def activate(self, proxy, sid, target, ifrom=None, block=True, timeout=None, callback=None):
        """Activate the socks5 session that has been negotiated."""
        iq = self.xmpp.Iq(sto=proxy, stype='set', sfrom=ifrom)
        iq['socks']['sid'] = sid
        iq['socks']['activate'] = target
        iq.send(block=block, timeout=timeout, callback=callback)

    def deactivate(self, sid):
        """Closes the proxy socket associated with this SID."""
        sock = self._sessions.get(sid)
        if sock:
            try:
                # sock.close() will also delete sid from self._sessions (see _connect_proxy)
                sock.close()
            except socket.error:
                pass
            # Though this should not be neccessary remove the closed session anyway
            with self._sessions_lock:
                if sid in self._sessions:
                    log.warn(('SOCKS5 session with sid = "%s" was not ' +
                              'removed from _sessions by sock.close()') % sid)
                    del self._sessions[sid]

    def close(self):
        """Closes all proxy sockets."""
        for sid, sock in self._sessions.items():
            sock.close()
        with self._sessions_lock:
            self._sessions = {}

    def _connect_proxy(self, sid, requester, target, proxy, proxy_port, peer=None):
        """ Establishes a connection between the client and the server-side
        Socks5 proxy.

        sid        : The StreamID. <str>
        requester  : The JID of the requester. <str>
        target     : The JID of the target. <str>
        proxy_host : The hostname or the IP of the proxy. <str>
        proxy_port : The port of the proxy. <str> or <int>
        peer       : The JID for the other side of the stream, regardless
                     of target or requester status.
        """
        # Because the xep_0065 plugin uses the proxy_port as string,
        # the Proxy class accepts the proxy_port argument as a string
        # or an integer. Here, we force to use the port as an integer.
        proxy_port = int(proxy_port)

        sock = socksocket()
        sock.setproxy(PROXY_TYPE_SOCKS5, proxy, port=proxy_port)

        # The hostname MUST be SHA1(SID + Requester JID + Target JID)
        # where the output is hexadecimal-encoded (not binary).
        digest = sha1()
        digest.update(sid.encode('utf-8'))
        digest.update(str(requester).encode('utf-8'))
        digest.update(str(target).encode('utf-8'))

        dest = digest.hexdigest()

        # The port MUST be 0.
        sock.connect((dest, 0))
        log.info('Socket connected.')

        _close = sock.close
        def close(*args, **kwargs):
            with self._sessions_lock:
                if sid in self._sessions:
                    del self._sessions[sid]
            _close()
            log.info('Socket closed.')
        sock.close = close

        sock.peer_jid = peer
        sock.self_jid = target if requester == peer else requester

        self.xmpp.event('socks_connected', sid)
        return sock

    def _accept_stream(self, iq):
        receiver = iq['to']
        sender = iq['from']
        sid = iq['socks']['sid']

        if self.api['authorized_sid'](receiver, sid, sender, iq):
            return True
        return self.api['authorized'](receiver, sid, sender, iq)

    def _authorized(self, jid, sid, ifrom, iq):
        return self.auto_accept

    def _authorized_sid(self, jid, sid, ifrom, iq):
        with self._preauthed_sids_lock:
            log.debug('>>> authed sids: %s', self._preauthed_sids)
            log.debug('>>> lookup: %s %s %s', jid, sid, ifrom)
            if (jid, sid, ifrom) in self._preauthed_sids:
                del self._preauthed_sids[(jid, sid, ifrom)]
                return True
            return False

    def _preauthorize_sid(self, jid, sid, ifrom, data):
        log.debug('>>>> %s %s %s %s', jid, sid, ifrom, data)
        with self._preauthed_sids_lock:
            self._preauthed_sids[(jid, sid, ifrom)] = True
