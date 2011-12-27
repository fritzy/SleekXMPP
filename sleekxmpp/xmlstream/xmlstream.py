# -*- coding: utf-8 -*-
"""
    sleekxmpp.xmlstream.xmlstream
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides the module for creating and
    interacting with generic XML streams, along with
    the necessary eventing infrastructure.

    Part of SleekXMPP: The Sleek XMPP Library

    :copyright: (c) 2011 Nathanael C. Fritz
    :license: MIT, see LICENSE for more details
"""

from __future__ import with_statement, unicode_literals

import base64
import copy
import logging
import signal
import socket as Socket
import ssl
import sys
import threading
import time
import types
import random
import weakref
try:
    import queue
except ImportError:
    import Queue as queue

import sleekxmpp
from sleekxmpp.thirdparty.statemachine import StateMachine
from sleekxmpp.xmlstream import Scheduler, tostring
from sleekxmpp.xmlstream.stanzabase import StanzaBase, ET
from sleekxmpp.xmlstream.handler import Waiter, XMLCallback
from sleekxmpp.xmlstream.matcher import MatchXMLMask

# In Python 2.x, file socket objects are broken. A patched socket
# wrapper is provided for this case in filesocket.py.
if sys.version_info < (3, 0):
    from sleekxmpp.xmlstream.filesocket import FileSocket, Socket26

try:
    import dns.resolver
except ImportError:
    DNSPYTHON = False
else:
    DNSPYTHON = True


#: The time in seconds to wait before timing out waiting for response stanzas.
RESPONSE_TIMEOUT = 30

#: The time in seconds to wait for events from the event queue, and also the
#: time between checks for the process stop signal.
WAIT_TIMEOUT = 1

#: The number of threads to use to handle XML stream events. This is not the
#: same as the number of custom event handling threads. 
#: :data:`HANDLER_THREADS` must be at least 1. For Python implementations
#: with a GIL, this should be left at 1, but for implemetnations without
#: a GIL increasing this value can provide better performance.
HANDLER_THREADS = 1

#: Flag indicating if the SSL library is available for use.
SSL_SUPPORT = True

#: The time in seconds to delay between attempts to resend data
#: after an SSL error.
SSL_RETRY_DELAY = 0.5

#: The maximum number of times to attempt resending data due to
#: an SSL error.
SSL_RETRY_MAX = 10

#: Maximum time to delay between connection attempts is one hour.
RECONNECT_MAX_DELAY = 600


log = logging.getLogger(__name__)


class RestartStream(Exception):
    """
    Exception to restart stream processing, including
    resending the stream header.
    """


class XMLStream(object):
    """
    An XML stream connection manager and event dispatcher.

    The XMLStream class abstracts away the issues of establishing a
    connection with a server and sending and receiving XML "stanzas".
    A stanza is a complete XML element that is a direct child of a root
    document element. Two streams are used, one for each communication
    direction, over the same socket. Once the connection is closed, both
    streams should be complete and valid XML documents.

    Three types of events are provided to manage the stream:
        :Stream: Triggered based on received stanzas, similar in concept
                 to events in a SAX XML parser.
        :Custom: Triggered manually.
        :Scheduled: Triggered based on time delays.

    Typically, stanzas are first processed by a stream event handler which
    will then trigger custom events to continue further processing,
    especially since custom event handlers may run in individual threads.

    :param socket: Use an existing socket for the stream. Defaults to
                   ``None`` to generate a new socket.
    :param string host: The name of the target server.
    :param int port: The port to use for the connection. Defaults to 0.
    """

    def __init__(self, socket=None, host='', port=0):
        #: Flag indicating if the SSL library is available for use.
        self.ssl_support = SSL_SUPPORT

        #: Most XMPP servers support TLSv1, but OpenFire in particular
        #: does not work well with it. For OpenFire, set 
        #: :attr:`ssl_version` to use ``SSLv23``::
        #:
        #:     import ssl
        #:     xmpp.ssl_version = ssl.PROTOCOL_SSLv23
        self.ssl_version = ssl.PROTOCOL_TLSv1

        #: Path to a file containing certificates for verifying the
        #: server SSL certificate. A non-``None`` value will trigger
        #: certificate checking.
        #: 
        #: .. note::
        #:
        #:     On Mac OS X, certificates in the system keyring will
        #:     be consulted, even if they are not in the provided file.
        self.ca_certs = None

        #: The time in seconds to wait for events from the event queue, 
        #: and also the time between checks for the process stop signal.
        self.wait_timeout = WAIT_TIMEOUT

        #: The time in seconds to wait before timing out waiting 
        #: for response stanzas.
        self.response_timeout = RESPONSE_TIMEOUT

        #: The current amount to time to delay attempting to reconnect. 
        #: This value doubles (with some jitter) with each failed
        #: connection attempt up to :attr:`reconnect_max_delay` seconds.
        self.reconnect_delay = None
            
        #: Maximum time to delay between connection attempts is one hour.
        self.reconnect_max_delay = RECONNECT_MAX_DELAY

        #: The time in seconds to delay between attempts to resend data
        #: after an SSL error.
        self.ssl_retry_max = SSL_RETRY_MAX

        #: The maximum number of times to attempt resending data due to
        #: an SSL error.
        self.ssl_retry_delay = SSL_RETRY_DELAY

        #: The connection state machine tracks if the stream is
        #: ``'connected'`` or ``'disconnected'``.
        self.state = StateMachine(('disconnected', 'connected'))
        self.state._set_state('disconnected')

        #: The default port to return when querying DNS records.
        self.default_port = int(port)
        
        #: The domain to try when querying DNS records. 
        self.default_domain = ''
    
        #: The desired, or actual, address of the connected server.
        self.address = (host, int(port))
        
        #: A file-like wrapper for the socket for use with the
        #: :mod:`~xml.etree.ElementTree` module.
        self.filesocket = None
        self.set_socket(socket)

        if sys.version_info < (3, 0):
            self.socket_class = Socket26
        else:
            self.socket_class = Socket.socket

        #: Enable connecting to the server directly over SSL, in
        #: particular when the service provides two ports: one for
        #: non-SSL traffic and another for SSL traffic.
        self.use_ssl = False

        #: Enable connecting to the service without using SSL
        #: immediately, but allow upgrading the connection later
        #: to use SSL.
        self.use_tls = False

        #: If set to ``True``, attempt to connect through an HTTP
        #: proxy based on the settings in :attr:`proxy_config`.
        self.use_proxy = False

        #: An optional dictionary of proxy settings. It may provide:
        #: :host: The host offering proxy services.
        #: :port: The port for the proxy service.
        #: :username: Optional username for accessing the proxy.
        #: :password: Optional password for accessing the proxy.
        self.proxy_config = {}

        #: The default namespace of the stream content, not of the
        #: stream wrapper itself.
        self.default_ns = ''

        #: The namespace of the enveloping stream element.
        self.stream_ns = ''

        #: The default opening tag for the stream element.
        self.stream_header = "<stream>"

        #: The default closing tag for the stream element.
        self.stream_footer = "</stream>"

        #: If ``True``, periodically send a whitespace character over the
        #: wire to keep the connection alive. Mainly useful for connections
        #: traversing NAT.
        self.whitespace_keepalive = True

        #: The default interval between keepalive signals when
        #: :attr:`whitespace_keepalive` is enabled.
        self.whitespace_keepalive_interval = 300

        #: An :class:`~threading.Event` to signal that the application
        #: is stopping, and that all threads should shutdown.
        self.stop = threading.Event()

        #: An :class:`~threading.Event` to signal receiving a closing
        #: stream tag from the server.
        self.stream_end_event = threading.Event()
        self.stream_end_event.set()

        #: An :class:`~threading.Event` to signal the start of a stream
        #: session. Until this event fires, the send queue is not used
        #: and data is sent immediately over the wire.
        self.session_started_event = threading.Event()

        #: The default time in seconds to wait for a session to start 
        #: after connecting before reconnecting and trying again.
        self.session_timeout = 45

        #: A queue of stream, custom, and scheduled events to be processed.
        self.event_queue = queue.Queue()

        #: A queue of string data to be sent over the stream.
        self.send_queue = queue.Queue()

        #: A :class:`~sleekxmpp.xmlstream.scheduler.Scheduler` instance for
        #: executing callbacks in the future based on time delays.
        self.scheduler = Scheduler(self.stop)
        self.__failed_send_stanza = None

        #: A mapping of XML namespaces to well-known prefixes.
        self.namespace_map = {StanzaBase.xml_ns: 'xml'}

        self.__thread = {}
        self.__root_stanza = []
        self.__handlers = []
        self.__event_handlers = {}
        self.__event_handlers_lock = threading.Lock()

        self._id = 0
        self._id_lock = threading.Lock()

        #: The :attr:`auto_reconnnect` setting controls whether or not
        #: the stream will be restarted in the event of an error.
        self.auto_reconnect = True

        #: The :attr:`disconnect_wait` setting is the default value
        #: for controlling if the system waits for the send queue to
        #: empty before ending the stream. This may be overridden by
        #: passing ``wait=True`` or ``wait=False`` to :meth:`disconnect`.
        #: The default :attr:`disconnect_wait` value is ``False``.
        self.disconnect_wait = False

        #: A list of DNS results that have not yet been tried.
        self.dns_answers = []

        self.add_event_handler('connected', self._handle_connected)
        self.add_event_handler('session_start', self._start_keepalive)
        self.add_event_handler('session_end', self._end_keepalive)

    def use_signals(self, signals=None):
        """Register signal handlers for ``SIGHUP`` and ``SIGTERM``.

        By using signals, a ``'killed'`` event will be raised when the
        application is terminated.

        If a signal handler already existed, it will be executed first,
        before the ``'killed'`` event is raised.

        :param list signals: A list of signal names to be monitored.
                             Defaults to ``['SIGHUP', 'SIGTERM']``.
        """
        if signals is None:
            signals = ['SIGHUP', 'SIGTERM']

        existing_handlers = {}
        for sig_name in signals:
            if hasattr(signal, sig_name):
                sig = getattr(signal, sig_name)
                handler = signal.getsignal(sig)
                if handler:
                    existing_handlers[sig] = handler

        def handle_kill(signum, frame):
            """
            Capture kill event and disconnect cleanly after first
            spawning the ``'killed'`` event.
            """

            if signum in existing_handlers and \
                   existing_handlers[signum] != handle_kill:
                existing_handlers[signum](signum, frame)

            self.event("killed", direct=True)
            self.disconnect()

        try:
            for sig_name in signals:
                if hasattr(signal, sig_name):
                    sig = getattr(signal, sig_name)
                    signal.signal(sig, handle_kill)
            self.__signals_installed = True
        except:
            log.debug("Can not set interrupt signal handlers. " + \
                      "SleekXMPP is not running from a main thread.")

    def new_id(self):
        """Generate and return a new stream ID in hexadecimal form.

        Many stanzas, handlers, or matchers may require unique
        ID values. Using this method ensures that all new ID values
        are unique in this stream.
        """
        with self._id_lock:
            self._id += 1
            return self.get_id()

    def get_id(self):
        """Return the current unique stream ID in hexadecimal form."""
        return "%X" % self._id

    def connect(self, host='', port=0, use_ssl=False,
                use_tls=True, reattempt=True):
        """Create a new socket and connect to the server.

        Setting ``reattempt`` to ``True`` will cause connection attempts to
        be made every second until a successful connection is established.

        :param host: The name of the desired server for the connection.
        :param port: Port to connect to on the server.
        :param use_ssl: Flag indicating if SSL should be used by connecting
                        directly to a port using SSL.
        :param use_tls: Flag indicating if TLS should be used, allowing for
                        connecting to a port without using SSL immediately and
                        later upgrading the connection.
        :param reattempt: Flag indicating if the socket should reconnect
                          after disconnections.
        """
        if host and port:
            self.address = (host, int(port))
        try:
            Socket.inet_aton(self.address[0])
        except Socket.error:
            self.default_domain = self.address[0]

        # Respect previous SSL and TLS usage directives.
        if use_ssl is not None:
            self.use_ssl = use_ssl
        if use_tls is not None:
            self.use_tls = use_tls

        # Repeatedly attempt to connect until a successful connection
        # is established.
        connected = self.state.transition('disconnected', 'connected',
                                          func=self._connect)
        while reattempt and not connected and not self.stop.is_set():
            connected = self.state.transition('disconnected', 'connected',
                                              func=self._connect)
        return connected

    def _connect(self):
        self.scheduler.remove('Session timeout check')
        self.stop.clear()
        if self.default_domain:
            self.address = self.pick_dns_answer(self.default_domain,
                                                self.address[1])
        self.socket = self.socket_class(Socket.AF_INET, Socket.SOCK_STREAM)
        self.configure_socket()

        if self.reconnect_delay is None:
            delay = 1.0
        else:
            delay = min(self.reconnect_delay * 2, self.reconnect_max_delay)
            delay = random.normalvariate(delay, delay * 0.1)
            log.debug('Waiting %s seconds before connecting.', delay)
            elapsed = 0
            try:
                while elapsed < delay and not self.stop.is_set():
                    time.sleep(0.1)
                    elapsed += 0.1
            except KeyboardInterrupt:
                self.stop.set()
                return False
            except SystemExit:
                self.stop.set()
                return False

        if self.use_proxy:
            connected = self._connect_proxy()
            if not connected:
                self.reconnect_delay = delay
                return False

        if self.use_ssl and self.ssl_support:
            log.debug("Socket Wrapped for SSL")
            if self.ca_certs is None:
                cert_policy = ssl.CERT_NONE
            else:
                cert_policy = ssl.CERT_REQUIRED

            ssl_socket = ssl.wrap_socket(self.socket,
                                         ca_certs=self.ca_certs,
                                         cert_reqs=cert_policy)

            if hasattr(self.socket, 'socket'):
                # We are using a testing socket, so preserve the top
                # layer of wrapping.
                self.socket.socket = ssl_socket
            else:
                self.socket = ssl_socket

        try:
            if not self.use_proxy:
                log.debug("Connecting to %s:%s", *self.address)
                self.socket.connect(self.address)

            self.set_socket(self.socket, ignore=True)
            #this event is where you should set your application state
            self.event("connected", direct=True)
            self.reconnect_delay = 1.0
            return True
        except Socket.error as serr:
            error_msg = "Could not connect to %s:%s. Socket Error #%s: %s"
            self.event('socket_error', serr)
            log.error(error_msg, self.address[0], self.address[1],
                                 serr.errno, serr.strerror)
            self.reconnect_delay = delay
            return False

    def _connect_proxy(self):
        """Attempt to connect using an HTTP Proxy."""

        # Extract the proxy address, and optional credentials
        address = (self.proxy_config['host'], int(self.proxy_config['port']))
        cred = None
        if self.proxy_config['username']:
            username = self.proxy_config['username']
            password = self.proxy_config['password']

            cred = '%s:%s' % (username, password)
            if sys.version_info < (3, 0):
                cred = bytes(cred)
            else:
                cred = bytes(cred, 'utf-8')
            cred = base64.b64encode(cred).decode('utf-8')

        # Build the HTTP headers for connecting to the XMPP server
        headers = ['CONNECT %s:%s HTTP/1.0' % self.address,
                   'Host: %s:%s' % self.address,
                   'Proxy-Connection: Keep-Alive',
                   'Pragma: no-cache',
                   'User-Agent: SleekXMPP/%s' % sleekxmpp.__version__]
        if cred:
            headers.append('Proxy-Authorization: Basic %s' % cred)
        headers = '\r\n'.join(headers) + '\r\n\r\n'

        try:
            log.debug("Connecting to proxy: %s:%s", address)
            self.socket.connect(address)
            self.send_raw(headers, now=True)
            resp = ''
            while '\r\n\r\n' not in resp and not self.stop.is_set():
                resp += self.socket.recv(1024).decode('utf-8')
            log.debug('RECV: %s', resp)

            lines = resp.split('\r\n')
            if '200' not in lines[0]:
                self.event('proxy_error', resp)
                log.error('Proxy Error: %s', lines[0])
                return False

            # Proxy connection established, continue connecting
            # with the XMPP server.
            return True
        except Socket.error as serr:
            error_msg = "Could not connect to %s:%s. Socket Error #%s: %s"
            self.event('socket_error', serr)
            log.error(error_msg, self.address[0], self.address[1],
                                 serr.errno, serr.strerror)
            return False

    def _handle_connected(self, event=None):
        """
        Add check to ensure that a session is established within
        a reasonable amount of time.
        """

        def _handle_session_timeout():
            if not self.session_started_event.is_set():
                log.debug("Session start has taken more " + \
                          "than %d seconds", self.session_timeout)
                self.disconnect(reconnect=self.auto_reconnect)

        self.schedule("Session timeout check",
                self.session_timeout,
                _handle_session_timeout)

    def disconnect(self, reconnect=False, wait=None):
        """Terminate processing and close the XML streams.

        Optionally, the connection may be reconnected and
        resume processing afterwards.

        If the disconnect should take place after all items
        in the send queue have been sent, use ``wait=True``.
        
        .. warning::

            If you are constantly adding items to the queue
            such that it is never empty, then the disconnect will
            not occur and the call will continue to block.

        :param reconnect: Flag indicating if the connection
                          and processing should be restarted.
                          Defaults to ``False``.
        :param wait: Flag indicating if the send queue should
                     be emptied before disconnecting, overriding
                     :attr:`disconnect_wait`.
        """
        self.state.transition('connected', 'disconnected',
                              func=self._disconnect, args=(reconnect, wait))

    def _disconnect(self, reconnect=False, wait=None):
        self.event('session_end', direct=True)

        # Wait for the send queue to empty.
        if wait is not None:
            if wait:
                self.send_queue.join()
        elif self.disconnect_wait:
            self.send_queue.join()

        # Send the end of stream marker.
        self.send_raw(self.stream_footer, now=True)
        self.session_started_event.clear()
        # Wait for confirmation that the stream was
        # closed in the other direction.
        self.auto_reconnect = reconnect
        log.debug('Waiting for %s from server', self.stream_footer)
        self.stream_end_event.wait(4)
        if not self.auto_reconnect:
            self.stop.set()
        try:
            self.socket.shutdown(Socket.SHUT_RDWR)
            self.socket.close()
            self.filesocket.close()
        except Socket.error as serr:
            self.event('socket_error', serr)
        finally:
            #clear your application state
            self.event("disconnected", direct=True)
            return True

    def reconnect(self, reattempt=True):
        """Reset the stream's state and reconnect to the server."""
        log.debug("reconnecting...")
        if self.state.ensure('connected'):
            self.state.transition('connected', 'disconnected', wait=2.0,
                                  func=self._disconnect, args=(True,))

        log.debug("connecting...")
        connected = self.state.transition('disconnected', 'connected',
                                          wait=2.0, func=self._connect)
        while reattempt and not connected and not self.stop.is_set():
            connected = self.state.transition('disconnected', 'connected',
                                              wait=2.0, func=self._connect)
            connected = connected or self.state.ensure('connected')
        return connected

    def set_socket(self, socket, ignore=False):
        """Set the socket to use for the stream.

        The filesocket will be recreated as well.

        :param socket: The new socket object to use.
        :param bool ignore: If ``True``, don't set the connection
                            state to ``'connected'``.
        """
        self.socket = socket
        if socket is not None:
            # ElementTree.iterparse requires a file.
            # 0 buffer files have to be binary.

            # Use the correct fileobject type based on the Python
            # version to work around a broken implementation in
            # Python 2.x.
            if sys.version_info < (3, 0):
                self.filesocket = FileSocket(self.socket)
            else:
                self.filesocket = self.socket.makefile('rb', 0)
            if not ignore:
                self.state._set_state('connected')

    def configure_socket(self):
        """Set timeout and other options for self.socket.

        Meant to be overridden.
        """
        self.socket.settimeout(None)

    def configure_dns(self, resolver, domain=None, port=None):
        """
        Configure and set options for a :class:`~dns.resolver.Resolver`
        instance, and other DNS related tasks. For example, you
        can also check :meth:`~socket.socket.getaddrinfo` to see 
        if you need to call out to ``libresolv.so.2`` to 
        run ``res_init()``.

        Meant to be overridden.

        :param resolver: A :class:`~dns.resolver.Resolver` instance
                         or ``None`` if ``dnspython`` is not installed.
        :param domain: The initial domain under consideration.
        :param port: The initial port under consideration.
        """
        pass

    def start_tls(self):
        """Perform handshakes for TLS.

        If the handshake is successful, the XML stream will need
        to be restarted.
        """
        if self.ssl_support:
            log.info("Negotiating TLS")
            log.info("Using SSL version: %s", str(self.ssl_version))
            if self.ca_certs is None:
                cert_policy = ssl.CERT_NONE
            else:
                cert_policy = ssl.CERT_REQUIRED

            ssl_socket = ssl.wrap_socket(self.socket,
                                         ssl_version=self.ssl_version,
                                         do_handshake_on_connect=False,
                                         ca_certs=self.ca_certs,
                                         cert_reqs=cert_policy)

            if hasattr(self.socket, 'socket'):
                # We are using a testing socket, so preserve the top
                # layer of wrapping.
                self.socket.socket = ssl_socket
            else:
                self.socket = ssl_socket
            self.socket.do_handshake()
            self.set_socket(self.socket)
            return True
        else:
            log.warning("Tried to enable TLS, but ssl module not found.")
            return False

    def _start_keepalive(self, event):
        """Begin sending whitespace periodically to keep the connection alive.

        May be disabled by setting::

            self.whitespace_keepalive = False

        The keepalive interval can be set using::

            self.whitespace_keepalive_interval = 300
        """

        def send_keepalive():
            if self.send_queue.empty():
                self.send_raw(' ')

        self.schedule('Whitespace Keepalive',
                      self.whitespace_keepalive_interval,
                      send_keepalive,
                      repeat=True)

    def _end_keepalive(self, event):
        """Stop sending whitespace keepalives"""
        self.scheduler.remove('Whitespace Keepalive')

    def start_stream_handler(self, xml):
        """Perform any initialization actions, such as handshakes, 
        once the stream header has been sent.

        Meant to be overridden.
        """
        pass

    def register_stanza(self, stanza_class):
        """Add a stanza object class as a known root stanza. 
        
        A root stanza is one that appears as a direct child of the stream's
        root element.

        Stanzas that appear as substanzas of a root stanza do not need to
        be registered here. That is done using register_stanza_plugin() from
        sleekxmpp.xmlstream.stanzabase.

        Stanzas that are not registered will not be converted into
        stanza objects, but may still be processed using handlers and
        matchers.

        :param stanza_class: The top-level stanza object's class.
        """
        self.__root_stanza.append(stanza_class)

    def remove_stanza(self, stanza_class):
        """Remove a stanza from being a known root stanza. 
        
        A root stanza is one that appears as a direct child of the stream's
        root element.

        Stanzas that are not registered will not be converted into
        stanza objects, but may still be processed using handlers and
        matchers.
        """
        del self.__root_stanza[stanza_class]

    def add_handler(self, mask, pointer, name=None, disposable=False,
                    threaded=False, filter=False, instream=False):
        """A shortcut method for registering a handler using XML masks.

        The use of :meth:`register_handler()` is preferred.

        :param mask: An XML snippet matching the structure of the
                     stanzas that will be passed to this handler.
        :param pointer: The handler function itself.
        :parm name: A unique name for the handler. A name will
                    be generated if one is not provided.
        :param disposable: Indicates if the handler should be discarded
                           after one use.
        :param threaded: **DEPRECATED**.
                       Remains for backwards compatibility.
        :param filter: **DEPRECATED**.
                       Remains for backwards compatibility.
        :param instream: Indicates if the handler should execute during
                         stream processing and not during normal event
                         processing.
        """
        # To prevent circular dependencies, we must load the matcher
        # and handler classes here.

        if name is None:
            name = 'add_handler_%s' % self.getNewId()
        self.registerHandler(XMLCallback(name, MatchXMLMask(mask), pointer,
                                         once=disposable, instream=instream))

    def register_handler(self, handler, before=None, after=None):
        """Add a stream event handler that will be executed when a matching
        stanza is received.

        :param handler: The :class:`~sleekxmpp.xmlstream.handler.base.BaseHandler`
                        derived object to execute.
        """
        if handler.stream is None:
            self.__handlers.append(handler)
            handler.stream = weakref.ref(self)

    def remove_handler(self, name):
        """Remove any stream event handlers with the given name.

        :param name: The name of the handler.
        """
        idx = 0
        for handler in self.__handlers:
            if handler.name == name:
                self.__handlers.pop(idx)
                return True
            idx += 1
        return False

    def get_dns_records(self, domain, port=None):
        """Get the DNS records for a domain.

        :param domain: The domain in question.
        :param port: If the results don't include a port, use this one.
        """
        if port is None:
            port = self.default_port
        if DNSPYTHON:
            resolver = dns.resolver.get_default_resolver()
            self.configure_dns(resolver, domain=domain, port=port)

            try:
                answers = resolver.query(domain, dns.rdatatype.A)
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                log.warning("No A records for %s", domain)
                return [((domain, port), 0, 0)]
            except dns.exception.Timeout:
                log.warning("DNS resolution timed out " + \
                            "for A record of %s", domain)
                return [((domain, port), 0, 0)]
            else:
                return [((ans.address, port), 0, 0) for ans in answers]
        else:
            log.warning("dnspython is not installed -- " + \
                        "relying on OS A record resolution")
            self.configure_dns(None, domain=domain, port=port)
            return [((domain, port), 0, 0)]

    def pick_dns_answer(self, domain, port=None):
        """Pick a server and port from DNS answers.

        Gets DNS answers if none available.
        Removes used answer from available answers.

        :param domain: The domain in question.
        :param port: If the results don't include a port, use this one.
        """
        if not self.dns_answers:
            self.dns_answers = self.get_dns_records(domain, port)
        addresses = {}
        intmax = 0
        topprio = 65535
        for answer in self.dns_answers:
            topprio = min(topprio, answer[1])
        for answer in self.dns_answers:
            if answer[1] == topprio:
                intmax += answer[2]
                addresses[intmax] = answer[0]

        #python3 returns a generator for dictionary keys
        items = [x for x in addresses.keys()]
        items.sort()

        picked = random.randint(0, intmax)
        for item in items:
            if picked <= item:
                address = addresses[item]
                break
        for idx, answer in enumerate(self.dns_answers):
            if self.dns_answers[0] == address:
                break
        self.dns_answers.pop(idx)
        log.debug("Trying to connect to %s:%s", *address)
        return address

    def add_event_handler(self, name, pointer,
                          threaded=False, disposable=False):
        """Add a custom event handler that will be executed whenever
        its event is manually triggered.

        :param name: The name of the event that will trigger
                     this handler.
        :param pointer: The function to execute.
        :param threaded: If set to ``True``, the handler will execute
                         in its own thread. Defaults to ``False``.
        :param disposable: If set to ``True``, the handler will be
                           discarded after one use. Defaults to ``False``.
        """
        if not name in self.__event_handlers:
            self.__event_handlers[name] = []
        self.__event_handlers[name].append((pointer, threaded, disposable))

    def del_event_handler(self, name, pointer):
        """Remove a function as a handler for an event.

        :param name: The name of the event.
        :param pointer: The function to remove as a handler.
        """
        if not name in self.__event_handlers:
            return

        # Need to keep handlers that do not use
        # the given function pointer
        def filter_pointers(handler):
            return handler[0] != pointer

        self.__event_handlers[name] = list(filter(
            filter_pointers,
            self.__event_handlers[name]))

    def event_handled(self, name):
        """Returns the number of registered handlers for an event.

        :param name: The name of the event to check.
        """
        return len(self.__event_handlers.get(name, []))

    def event(self, name, data={}, direct=False):
        """Manually trigger a custom event.

        :param name: The name of the event to trigger.
        :param data: Data that will be passed to each event handler.
                     Defaults to an empty dictionary, but is usually
                     a stanza object.
        :param direct: Runs the event directly if True, skipping the
                       event queue. All event handlers will run in the
                       same thread.
        """
        handlers = self.__event_handlers.get(name, [])
        for handler in handlers:
            #TODO:  Data should not be copied, but should be read only,
            #       but this might break current code so it's left for future.

            out_data = copy.copy(data) if len(handlers) > 1 else data
            old_exception = getattr(data, 'exception', None)
            if direct:
                try:
                    handler[0](out_data)
                except Exception as e:
                    error_msg = 'Error processing event handler: %s'
                    log.exception(error_msg,  str(handler[0]))
                    if old_exception:
                        old_exception(e)
                    else:
                        self.exception(e)
            else:
                self.event_queue.put(('event', handler, out_data))
            if handler[2]:
                # If the handler is disposable, we will go ahead and
                # remove it now instead of waiting for it to be
                # processed in the queue.
                with self.__event_handlers_lock:
                    try:
                        h_index = self.__event_handlers[name].index(handler)
                        self.__event_handlers[name].pop(h_index)
                    except:
                        pass

    def schedule(self, name, seconds, callback, args=None,
                 kwargs=None, repeat=False):
        """Schedule a callback function to execute after a given delay.

        :param name: A unique name for the scheduled callback.
        :param  seconds: The time in seconds to wait before executing.
        :param callback: A pointer to the function to execute.
        :param args: A tuple of arguments to pass to the function.
        :param kwargs: A dictionary of keyword arguments to pass to
                       the function.
        :param repeat: Flag indicating if the scheduled event should
                       be reset and repeat after executing.
        """
        self.scheduler.add(name, seconds, callback, args, kwargs,
                           repeat, qpointer=self.event_queue)

    def incoming_filter(self, xml):
        """Filter incoming XML objects before they are processed.

        Possible uses include remapping namespaces, or correcting elements
        from sources with incorrect behavior.

        Meant to be overridden.
        """
        return xml

    def send(self, data, mask=None, timeout=None, now=False):
        """A wrapper for :meth:`send_raw()` for sending stanza objects.

        May optionally block until an expected response is received.

        :param data: The :class:`~sleekxmpp.xmlstream.stanzabase.ElementBase` 
                     stanza to send on the stream.
        :param mask: **DEPRECATED** 
                     An XML string snippet matching the structure
                     of the expected response. Execution will block
                     in this thread until the response is received
                     or a timeout occurs.
        :param int timeout: Time in seconds to wait for a response before
                       continuing. Defaults to :attr:`response_timeout`.
        :param bool now: Indicates if the send queue should be skipped,
                        sending the stanza immediately. Useful mainly
                        for stream initialization stanzas.
                        Defaults to ``False``.
        """
        if timeout is None:
            timeout = self.response_timeout
        if hasattr(mask, 'xml'):
            mask = mask.xml
        data = str(data)
        if mask is not None:
            log.warning("Use of send mask waiters is deprecated.")
            wait_for = Waiter("SendWait_%s" % self.new_id(),
                              MatchXMLMask(mask))
            self.register_handler(wait_for)
        self.send_raw(data, now)
        if mask is not None:
            return wait_for.wait(timeout)

    def send_xml(self, data, mask=None, timeout=None, now=False):
        """Send an XML object on the stream, and optionally wait
        for a response.

        :param data: The :class:`~xml.etree.ElementTree.Element` XML object 
                     to send on the stream.
        :param mask: **DEPRECATED** 
                     An XML string snippet matching the structure
                     of the expected response. Execution will block
                     in this thread until the response is received
                     or a timeout occurs.
        :param int timeout: Time in seconds to wait for a response before
                       continuing. Defaults to :attr:`response_timeout`.
        :param bool now: Indicates if the send queue should be skipped,
                        sending the stanza immediately. Useful mainly
                        for stream initialization stanzas.
                        Defaults to ``False``.
        """
        if timeout is None:
            timeout = self.response_timeout
        return self.send(tostring(data), mask, timeout, now)

    def send_raw(self, data, now=False, reconnect=None):
        """Send raw data across the stream.

        :param string data: Any string value.
        :param bool reconnect: Indicates if the stream should be
                               restarted if there is an error sending
                               the stanza. Used mainly for testing.
                               Defaults to :attr:`auto_reconnect`.
        """
        if now:
            log.debug("SEND (IMMED): %s", data)
            try:
                data = data.encode('utf-8')
                total = len(data)
                sent = 0
                count = 0
                tries = 0
                while sent < total and not self.stop.is_set():
                    try:
                        sent += self.socket.send(data[sent:])
                        count += 1
                    except ssl.SSLError as serr:
                        if tries >= self.ssl_retry_max:
                            log.debug('SSL error - max retries reached')
                            self.exception(serr)
                            log.warning("Failed to send %s", data)
                            if reconnect is None:
                                reconnect = self.auto_reconnect
                            self.disconnect(reconnect)
                        log.warning('SSL write error - reattempting')
                        time.sleep(self.ssl_retry_delay)
                        tries += 1
                if count > 1:
                    log.debug('SENT: %d chunks', count)
            except Socket.error as serr:
                self.event('socket_error', serr)
                log.warning("Failed to send %s", data)
                if reconnect is None:
                    reconnect = self.auto_reconnect
                self.disconnect(reconnect)
        else:
            self.send_queue.put(data)
        return True

    def process(self, **kwargs):
        """Initialize the XML streams and begin processing events.

        The number of threads used for processing stream events is determined
        by :data:`HANDLER_THREADS`.

        :param bool block: If ``False``, then event dispatcher will run
                    in a separate thread, allowing for the stream to be
                    used in the background for another application.
                    Otherwise, ``process(block=True)`` blocks the current
                    thread. Defaults to ``False``.
        :param bool threaded: **DEPRECATED**
                    If ``True``, then event dispatcher will run
                    in a separate thread, allowing for the stream to be
                    used in the background for another application.
                    Defaults to ``True``. This does **not** mean that no
                    threads are used at all if ``threaded=False``.

        Regardless of these threading options, these threads will 
        always exist:

        - The event queue processor
        - The send queue processor
        - The scheduler
        """
        if 'threaded' in kwargs and 'block' in kwargs:
            raise ValueError("process() called with both " + \
                             "block and threaded arguments")
        elif 'block' in kwargs:
            threaded = not(kwargs.get('block', False))
        else:
            threaded = kwargs.get('threaded', True)

        self.scheduler.process(threaded=True)

        def start_thread(name, target):
            self.__thread[name] = threading.Thread(name=name, target=target)
            self.__thread[name].start()

        for t in range(0, HANDLER_THREADS):
            log.debug("Starting HANDLER THREAD")
            start_thread('stream_event_handler_%s' % t, self._event_runner)

        start_thread('send_thread', self._send_thread)

        if threaded:
            # Run the XML stream in the background for another application.
            start_thread('process', self._process)
        else:
            self._process()

    def _process(self):
        """Start processing the XML streams.

        Processing will continue after any recoverable errors
        if reconnections are allowed.
        """

        # The body of this loop will only execute once per connection.
        # Additional passes will be made only if an error occurs and
        # reconnecting is permitted.
        while True:
            shutdown = False
            try:
                # The call to self.__read_xml will block and prevent
                # the body of the loop from running until a disconnect
                # occurs. After any reconnection, the stream header will
                # be resent and processing will resume.
                while not self.stop.is_set():
                    # Only process the stream while connected to the server
                    if not self.state.ensure('connected', wait=0.1,
                                             block_on_transition=True):
                        continue
                    # Ensure the stream header is sent for any
                    # new connections.
                    if not self.session_started_event.is_set():
                        self.send_raw(self.stream_header, now=True)
                    if not self.__read_xml():
                        # If the server terminated the stream, end processing
                        break
            except KeyboardInterrupt:
                log.debug("Keyboard Escape Detected in _process")
                self.event('killed', direct=True)
                shutdown = True
            except SystemExit:
                log.debug("SystemExit in _process")
                shutdown = True
            except SyntaxError as e:
                log.error("Error reading from XML stream.")
                shutdown = True
                self.exception(e)
            except Socket.error as serr:
                self.event('socket_error', serr)
                log.exception('Socket Error')
            except Exception as e:
                if not self.stop.is_set():
                    log.exception('Connection error.')
                self.exception(e)

            if not shutdown and not self.stop.is_set() \
               and self.auto_reconnect:
                self.reconnect()
            else:
                self.disconnect()
                break

    def __read_xml(self):
        """Parse the incoming XML stream
        
        Stream events are raised for each received stanza.
        """
        depth = 0
        root = None
        for event, xml in ET.iterparse(self.filesocket, (b'end', b'start')):
            if event == b'start':
                if depth == 0:
                    # We have received the start of the root element.
                    root = xml
                    # Perform any stream initialization actions, such
                    # as handshakes.
                    self.stream_end_event.clear()
                    self.start_stream_handler(root)
                depth += 1
            if event == b'end':
                depth -= 1
                if depth == 0:
                    # The stream's root element has closed,
                    # terminating the stream.
                    log.debug("End of stream recieved")
                    self.stream_end_event.set()
                    return False
                elif depth == 1:
                    # We only raise events for stanzas that are direct
                    # children of the root element.
                    try:
                        self.__spawn_event(xml)
                    except RestartStream:
                        return True
                    if root is not None:
                        # Keep the root element empty of children to
                        # save on memory use.
                        root.clear()
        log.debug("Ending read XML loop")

    def _build_stanza(self, xml, default_ns=None):
        """Create a stanza object from a given XML object.

        If a specialized stanza type is not found for the XML, then
        a generic :class:`~sleekxmpp.xmlstream.stanzabase.StanzaBase` 
        stanza will be returned.

        :param xml: The :class:`~xml.etree.ElementTree.Element` XML object 
                    to convert into a stanza object.
        :param default_ns: Optional default namespace to use instead of the
                           stream's current default namespace.
        """
        if default_ns is None:
            default_ns = self.default_ns
        stanza_type = StanzaBase
        for stanza_class in self.__root_stanza:
            if xml.tag == "{%s}%s" % (default_ns, stanza_class.name) or \
               xml.tag == stanza_class.tag_name():
                stanza_type = stanza_class
                break
        stanza = stanza_type(self, xml)
        return stanza

    def __spawn_event(self, xml):
        """
        Analyze incoming XML stanzas and convert them into stanza
        objects if applicable and queue stream events to be processed
        by matching handlers.

        :param xml: The :class:`~sleekxmpp.xmlstream.stanzabase.ElementBase`
                    stanza to analyze.
        """
        log.debug("RECV: %s", tostring(xml, xmlns=self.default_ns,
                                            stream=self))
        # Apply any preprocessing filters.
        xml = self.incoming_filter(xml)

        # Convert the raw XML object into a stanza object. If no registered
        # stanza type applies, a generic StanzaBase stanza will be used.
        stanza = self._build_stanza(xml)

        # Match the stanza against registered handlers. Handlers marked
        # to run "in stream" will be executed immediately; the rest will
        # be queued.
        unhandled = True
        matched_handlers = [h for h in self.__handlers if h.match(stanza)]
        for handler in matched_handlers:
            if len(matched_handlers) > 1:
                stanza_copy = copy.copy(stanza)
            else:
                stanza_copy = stanza
            handler.prerun(stanza_copy)
            self.event_queue.put(('stanza', handler, stanza_copy))
            try:
                if handler.check_delete():
                    self.__handlers.remove(handler)
            except:
                pass  # not thread safe
            unhandled = False

        # Some stanzas require responses, such as Iq queries. A default
        # handler will be executed immediately for this case.
        if unhandled:
            stanza.unhandled()

    def _threaded_event_wrapper(self, func, args):
        """Capture exceptions for event handlers that run
        in individual threads.

        :param func: The event handler to execute.
        :param args: Arguments to the event handler.
        """
        # this is always already copied before this is invoked
        orig = args[0]
        try:
            func(*args)
        except Exception as e:
            error_msg = 'Error processing event handler: %s'
            log.exception(error_msg, str(func))
            if hasattr(orig, 'exception'):
                orig.exception(e)
            else:
                self.exception(e)

    def _event_runner(self):
        """Process the event queue and execute handlers.

        The number of event runner threads is controlled by HANDLER_THREADS.

        Stream event handlers will all execute in this thread. Custom event
        handlers may be spawned in individual threads.
        """
        log.debug("Loading event runner")
        try:
            while not self.stop.is_set():
                try:
                    wait = self.wait_timeout
                    event = self.event_queue.get(True, timeout=wait)
                except queue.Empty:
                    event = None
                if event is None:
                    continue

                etype, handler = event[0:2]
                args = event[2:]
                orig = copy.copy(args[0])

                if etype == 'stanza':
                    try:
                        handler.run(args[0])
                    except Exception as e:
                        error_msg = 'Error processing stream handler: %s'
                        log.exception(error_msg, handler.name)
                        orig.exception(e)
                elif etype == 'schedule':
                    name = args[1]
                    try:
                        log.debug('Scheduled event: %s: %s', name, args[0])
                        handler(*args[0])
                    except Exception as e:
                        log.exception('Error processing scheduled task')
                        self.exception(e)
                elif etype == 'event':
                    func, threaded, disposable = handler
                    try:
                        if threaded:
                            x = threading.Thread(
                                    name="Event_%s" % str(func),
                                    target=self._threaded_event_wrapper,
                                    args=(func, args))
                            x.start()
                        else:
                            func(*args)
                    except Exception as e:
                        error_msg = 'Error processing event handler: %s'
                        log.exception(error_msg, str(func))
                        if hasattr(orig, 'exception'):
                            orig.exception(e)
                        else:
                            self.exception(e)
                elif etype == 'quit':
                    log.debug("Quitting event runner thread")
                    return False
        except KeyboardInterrupt:
            log.debug("Keyboard Escape Detected in _event_runner")
            self.event('killed', direct=True)
            self.disconnect()
            return
        except SystemExit:
            self.disconnect()
            self.event_queue.put(('quit', None, None))
            return

    def _send_thread(self):
        """Extract stanzas from the send queue and send them on the stream."""
        try:
            while not self.stop.is_set():
                while not self.stop.is_set and \
                      not self.session_started_event.is_set():
                    self.session_started_event.wait(timeout=1)
                if self.__failed_send_stanza is not None:
                    data = self.__failed_send_stanza
                    self.__failed_send_stanza = None
                else:
                    try:
                        data = self.send_queue.get(True, 1)
                    except queue.Empty:
                        continue
                log.debug("SEND: %s", data)
                enc_data = data.encode('utf-8')
                total = len(enc_data)
                sent = 0
                count = 0
                tries = 0
                try:
                    while sent < total and not self.stop.is_set():
                        try:
                            sent += self.socket.send(enc_data[sent:])
                            count += 1
                        except ssl.SSLError as serr:
                            if tries >= self.ssl_retry_max:
                                log.debug('SSL error - max retries reached')
                                self.exception(serr)
                                log.warning("Failed to send %s", data)
                                if reconnect is None:
                                    reconnect = self.auto_reconnect
                                self.disconnect(reconnect)
                            log.warning('SSL write error - reattempting')
                            time.sleep(self.ssl_retry_delay)
                            tries += 1
                    if count > 1:
                        log.debug('SENT: %d chunks', count)
                    self.send_queue.task_done()
                except Socket.error as serr:
                    self.event('socket_error', serr)
                    log.warning("Failed to send %s", data)
                    self.__failed_send_stanza = data
                    self.disconnect(self.auto_reconnect)
        except Exception as ex:
            log.exception('Unexpected error in send thread: %s', ex)
            self.exception(ex)
            if not self.stop.is_set():
                self.disconnect(self.auto_reconnect)

    def exception(self, exception):
        """Process an unknown exception.

        Meant to be overridden.

        :param exception: An unhandled exception object.
        """
        pass


# To comply with PEP8, method names now use underscores.
# Deprecated method names are re-mapped for backwards compatibility.
XMLStream.startTLS = XMLStream.start_tls
XMLStream.registerStanza = XMLStream.register_stanza
XMLStream.removeStanza = XMLStream.remove_stanza
XMLStream.registerHandler = XMLStream.register_handler
XMLStream.removeHandler = XMLStream.remove_handler
XMLStream.setSocket = XMLStream.set_socket
XMLStream.sendRaw = XMLStream.send_raw
XMLStream.getId = XMLStream.get_id
XMLStream.getNewId = XMLStream.new_id
XMLStream.sendXML = XMLStream.send_xml
