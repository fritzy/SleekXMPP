import sys
import logging
import struct

from threading import Thread, Event
from hashlib import sha1
from select import select
from uuid import uuid4

from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from socks import socksocket, PROXY_TYPE_SOCKS5

import stanza

# Registers the sleekxmpp logger
log = logging.getLogger(__name__)


class xep_0065(base_plugin):
    """
    XEP-0065 In-Band Bytestreams
    """

    description = "In-Band Bytestreams"
    dependencies = set(['xep_0030', ])
    xep = '0065'

    # A dict contains for each SID, the proxy thread currently
    # running.
    proxy_threads = {}

    def plugin_init(self):
        """ Initializes the xep_0065 plugin and all event callbacks.
        """

        # Shortcuts to access to the xep_0030 plugin.
        self.disco = self.xmpp['xep_0030']

        # Handler for the streamhost stanza.
        self.xmpp.registerHandler(
            Callback('In-Band Bytestreams',
                     StanzaPath('iq@type=set/q/streamhost'),
                     self._handle_streamhost))

        # Handler for the streamhost-used stanza.
        self.xmpp.registerHandler(
            Callback('In-Band Bytestreams',
                     StanzaPath('iq@type=result/q/streamhost-used'),
                     self._handle_streamhost_used))

    def handshake(self, to, streamer=None):
        """ Starts the handshake to establish the socks5 bytestreams
        connection.
        """

        # Discovers the proxy.
        self.streamer = streamer or self.discover_proxy()

        # Requester requests network address from the proxy.
        streamhost = self.get_network_address(self.streamer)
        self.proxy_host = streamhost['q']['streamhost']['host']
        self.proxy_port = streamhost['q']['streamhost']['port']

        # Generates the SID for this new handshake.
        sid = uuid4().hex

        # Requester initiates S5B negotation with Target by sending
        # IQ-set that includes the JabberID and network address of
        # StreamHost as well as the StreamID (SID) of the proposed
        # bytestream.
        iq = self.xmpp.Iq(sto=to, stype='set')
        iq['q']['sid'] = sid
        iq['q']['streamhost']['jid'] = self.streamer
        iq['q']['streamhost']['host'] = self.proxy_host
        iq['q']['streamhost']['port'] = self.proxy_port

        # Sends the new IQ.
        return iq.send()

    def discover_proxy(self):
        """ Auto-discovers (using XEP 0030) the available bytestream
        proxy on the XMPP server.

        Returns the JID of the proxy.
        """

        # Gets all disco items.
        disco_items = self.disco.get_items(self.xmpp.server)

        for item in disco_items['disco_items']['items']:
            # For each items, gets the disco info.
            disco_info = self.disco.get_info(item[0])

            # Gets and verifies if the identity is a bytestream proxy.
            identities = disco_info['disco_info']['identities']
            for identity in identities:
                if identity[0] == 'proxy' and identity[1] == 'bytestreams':
                    # Returns when the first occurence is found.
                    return '%s' % disco_info['from']

    def get_network_address(self, streamer):
        """ Gets the streamhost information of the proxy.

        streamer : The jid of the proxy.
        """

        iq = self.xmpp.Iq(sto=streamer, stype='get')
        iq['q']  # Adds the query eleme to the iq.

        return iq.send()

    def _handle_streamhost(self, iq):
        """ Handles all streamhost stanzas.
        """

        # Registers the streamhost info.
        self.streamer = iq['q']['streamhost']['jid']
        self.proxy_host = iq['q']['streamhost']['host']
        self.proxy_port = iq['q']['streamhost']['port']

        # Sets the SID, the requester and the target.
        sid = iq['q']['sid']
        requester = '%s' % iq['from']
        target = '%s' % self.xmpp.boundjid

        # Next the Target attempts to open a standard TCP socket on
        # the network address of the Proxy.
        self.proxy_thread = Proxy(sid, requester, target, self.proxy_host,
                                  self.proxy_port, self.on_recv)
        self.proxy_thread.start()

        # Registers the new thread in the proxy_thread dict.
        self.proxy_threads[sid] = self.proxy_thread

        # Wait until the proxy is connected
        self.proxy_thread.connected.wait()

        # Replies to the incoming iq with a streamhost-used stanza.
        res_iq = iq.reply()
        res_iq['q']['sid'] = sid
        res_iq['q']['streamhost-used']['jid'] = self.streamer

        # Sends the IQ
        return res_iq.send()

    def _handle_streamhost_used(self, iq):
        """ Handles all streamhost-used stanzas.
        """

        # Sets the SID, the requester and the target.
        sid = iq['q']['sid']
        requester = '%s' % self.xmpp.boundjid
        target  = '%s' % iq['from']

        # The Requester will establish a connection to the SOCKS5
        # proxy in the same way the Target did.
        self.proxy_thread = Proxy(sid, requester, target, self.proxy_host,
                                  self.proxy_port, self.on_recv)
        self.proxy_thread.start()

        # Registers the new thread in the proxy_thread dict.
        self.proxy_threads[sid] = self.proxy_thread

        # Wait until the proxy is connected
        self.proxy_thread.connected.wait()

        # Requester sends IQ-set to StreamHost requesting that
        # StreamHost activate the bytestream associated with the
        # StreamID.
        self.activate(iq['q']['sid'], target)

    def activate(self, sid, to):
        """ IQ-set to StreamHost requesting that StreamHost activate
        the bytestream associated with the StreamID.
        """

        # Creates the activate IQ.
        act_iq = self.xmpp.Iq(sto=self.streamer, stype='set')
        act_iq['q']['sid'] = sid
        act_iq['q']['activate'] = to

        # Send the IQ.
        act_iq.send()

    def send(self, sid, msg):
        """ Sends the msg to the socket.

        sid : The SID to retrieve the good proxy stored in the
              proxy_threads dict
        msg : The message data.
        """

        proxy = self.proxy_threads.get(sid)
        if proxy:
            proxy.send(msg)
        else:
            # TODO: raise an exception.
            pass

    def on_recv(self, sid, data):
        """ Called when receiving data
        """

        if not data:
            try:
                del self.proxy_threads[sid]
            except KeyError:
                # TODO: internal error, raise an exception ?
                pass
        else:
            log.debug('Received data: %s' % data)
            self.xmpp.event('socks_recv', data)


class Proxy(Thread):
    """ Establishes in a thread a connection between the client and
    the server-side Socks5 proxy.
    """

    def __init__(self, sid, requester, target, proxy, proxy_port,
                 on_recv):
        """ Initializes the proxy thread.

        sid        : The StreamID. <str>
        requester  : The JID of the requester. <str>
        target     : The JID of the target. <str>
        proxy_host : The hostname or the IP of the proxy. <str>
        proxy_port : The port of the proxy. <str> or <int>
        on_recv    : A callback called when data are received from the
                     socket. <Callable>
        """

        # Initializes the thread.
        Thread.__init__(self)

        # Because the xep_0065 plugin uses the proxy_port as string,
        # the Proxy class accepts the proxy_port argument as a string
        # or an integer. Here, we force to use the port as an integer.
        proxy_port = int(proxy_port)

        # Creates a connected event to warn when to proxy is
        # connected.
        self.connected = Event()

        # Registers the arguments.
        self.sid = sid
        self.requester = requester
        self.target = target
        self.proxy = proxy
        self.proxy_port = proxy_port
        self.on_recv = on_recv

    def run(self):
        """ Starts the thread.
        """

        # Creates the socks5 proxy socket
        self.s = socksocket()
        self.s.setproxy(PROXY_TYPE_SOCKS5, self.proxy, port=self.proxy_port)

        # The hostname MUST be SHA1(SID + Requester JID + Target JID)
        # where the output is hexadecimal-encoded (not binary).
        digest = sha1()
        digest.update(self.sid)  # SID
        digest.update(self.requester)  # Requester JID
        digest.update(self.target)  # Target JID

        # Computes the digest in hex.
        dest = '%s' % digest.hexdigest()

        # The port MUST be 0.
        self.s.connect((dest, 0))
        log.info('Socket connected.')
        self.connected.set()

        # Listen for data on the socket
        self.listen()

        # Listen returns when the socket must be closed.
        self.s.close()
        log.info('Socket closed.')

    def listen(self):
        """ Listen for data on the socket. When receiving data, call
        the callback on_recv callable.
        """

        socket_open = True
        while socket_open:
            ins, out, err = select([self.s, ], [], [])

            for s in ins:
                data = self.recv_size(self.s)
                if not data:
                    socket_open = False

                self.on_recv(self.sid, data)

    def recv_size(self, the_socket):
        total_len = 0
        total_data = []
        size = sys.maxint
        size_data = sock_data = ''
        recv_size = 8192

        while total_len < size:
            sock_data = the_socket.recv(recv_size)
            if not sock_data:
                return ''.join(total_data)

            if not total_data:
                if len(sock_data) > 4:
                    size_data += sock_data
                    size = struct.unpack('>i', size_data[:4])[0]
                    recv_size = size
                    if recv_size > 524288:
                        recv_size = 524288
                    total_data.append(size_data[4:])
                else:
                    size_data += sock_data
            else:
                total_data.append(sock_data)
            total_len = sum([len(i) for i in total_data])
        return ''.join(total_data)

    def send(self, msg):
        """ Sends the data over the socket.
        """

        self.s.sendall(msg)
