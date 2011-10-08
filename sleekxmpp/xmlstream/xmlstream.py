"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
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


# The time in seconds to wait before timing out waiting for response stanzas.
RESPONSE_TIMEOUT = 30

# The time in seconds to wait for events from the event queue, and also the
# time between checks for the process stop signal.
WAIT_TIMEOUT = 1

# The number of threads to use to handle XML stream events. This is not the
# same as the number of custom event handling threads. HANDLER_THREADS must
# be at least 1.
HANDLER_THREADS = 1

# Flag indicating if the SSL library is available for use.
SSL_SUPPORT = True

# Maximum time to delay between connection attempts is one hour.
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
        Stream    -- Triggered based on received stanzas, similar in concept
                     to events in a SAX XML parser.
        Custom    -- Triggered manually.
        Scheduled -- Triggered based on time delays.

    Typically, stanzas are first processed by a stream event handler which
    will then trigger custom events to continue further processing,
    especially since custom event handlers may run in individual threads.


    Attributes:
        address       -- The hostname and port of the server.
        default_ns    -- The default XML namespace that will be applied
                         to all non-namespaced stanzas.
        event_queue   -- A queue of stream, custom, and scheduled
                         events to be processed.
        filesocket    -- A filesocket created from the main connection socket.
                         Required for ElementTree.iterparse.
        default_port  -- Default port to connect to.
        namespace_map -- Optional mapping of namespaces to namespace prefixes.
        scheduler     -- A scheduler object for triggering events
                         after a given period of time.
        send_queue    -- A queue of stanzas to be sent on the stream.
        socket        -- The connection to the server.
        ssl_support   -- Indicates if a SSL library is available for use.
        ssl_version   -- The version of the SSL protocol to use.
                         Defaults to ssl.PROTOCOL_TLSv1.
        ca_certs      -- File path to a CA certificate to verify the
                         server's identity.
        state         -- A state machine for managing the stream's
                         connection state.
        stream_footer -- The start tag and any attributes for the stream's
                         root element.
        stream_header -- The closing tag of the stream's root element.
        use_ssl       -- Flag indicating if SSL should be used.
        use_tls       -- Flag indicating if TLS should be used.
        use_proxy     -- Flag indicating that an HTTP Proxy should be used.
        stop          -- threading Event used to stop all threads.
        proxy_config  -- An optional dictionary with the following entries:
                            host     -- The host offering proxy services.
                            port     -- The port for the proxy service.
                            username -- Optional username for the proxy.
                            password -- Optional password for the proxy.

        auto_reconnect      -- Flag to determine whether we auto reconnect.
        reconnect_max_delay -- Maximum time to delay between connection
                               attempts. Defaults to RECONNECT_MAX_DELAY,
                               which is one hour.
        dns_answers     -- List of dns answers not yet used to connect.

    Methods:
        add_event_handler    -- Add a handler for a custom event.
        add_handler          -- Shortcut method for registerHandler.
        connect              -- Connect to the given server.
        del_event_handler    -- Remove a handler for a custom event.
        disconnect           -- Disconnect from the server and terminate
                                processing.
        event                -- Trigger a custom event.
        get_id               -- Return the current stream ID.
        incoming_filter      -- Optionally filter stanzas before processing.
        new_id               -- Generate a new, unique ID value.
        process              -- Read XML stanzas from the stream and apply
                                matching stream handlers.
        reconnect            -- Reestablish a connection to the server.
        register_handler     -- Add a handler for a stream event.
        register_stanza      -- Add a new stanza object type that may appear
                                as a direct child of the stream's root.
        remove_handler       -- Remove a stream handler.
        remove_stanza        -- Remove a stanza object type.
        schedule             -- Schedule an event handler to execute after a
                                given delay.
        send                 -- Send a stanza object on the stream.
        send_raw             -- Send a raw string on the stream.
        send_xml             -- Send an XML string on the stream.
        set_socket           -- Set the stream's socket and generate a new
                                filesocket.
        start_stream_handler -- Perform any stream initialization such
                                as handshakes.
        start_tls            -- Establish a TLS connection and restart
                                the stream.
    """

    def __init__(self, socket=None, host='', port=0):
        """
        Establish a new XML stream.

        Arguments:
            socket -- Use an existing socket for the stream.
                      Defaults to None to generate a new socket.
            host   -- The name of the target server.
                      Defaults to the empty string.
            port   -- The port to use for the connection.
                      Defaults to 0.
        """
        self.ssl_support = SSL_SUPPORT
        self.ssl_version = ssl.PROTOCOL_TLSv1
        self.ca_certs = None

        self.wait_timeout = WAIT_TIMEOUT
        self.response_timeout = RESPONSE_TIMEOUT
        self.reconnect_delay = None
        self.reconnect_max_delay = RECONNECT_MAX_DELAY

        self.state = StateMachine(('disconnected', 'connected'))
        self.state._set_state('disconnected')

        self.default_port = int(port)
        self.default_domain = ''
        self.address = (host, int(port))
        self.filesocket = None
        self.set_socket(socket)

        if sys.version_info < (3, 0):
            self.socket_class = Socket26
        else:
            self.socket_class = Socket.socket

        self.use_ssl = False
        self.use_tls = False
        self.use_proxy = False

        self.proxy_config = {}

        self.default_ns = ''
        self.stream_ns = ''
        self.stream_header = "<stream>"
        self.stream_footer = "</stream>"

        self.whitespace_keepalive = True
        self.whitespace_keepalive_interval = 300

        self.stop = threading.Event()
        self.stream_end_event = threading.Event()
        self.stream_end_event.set()
        self.session_started_event = threading.Event()
        self.session_timeout = 45

        self.event_queue = queue.Queue()
        self.send_queue = queue.Queue()
        self.__failed_send_stanza = None
        self.scheduler = Scheduler(self.stop)

        self.namespace_map = {StanzaBase.xml_ns: 'xml'}

        self.__thread = {}
        self.__root_stanza = []
        self.__handlers = []
        self.__event_handlers = {}
        self.__event_handlers_lock = threading.Lock()

        self._id = 0
        self._id_lock = threading.Lock()

        self.auto_reconnect = True
        self.dns_answers = []

        self.add_event_handler('connected', self._handle_connected)
        self.add_event_handler('session_start', self._start_keepalive)
        self.add_event_handler('session_end', self._end_keepalive)

    def use_signals(self, signals=None):
        """
        Register signal handlers for SIGHUP and SIGTERM, if possible,
        which will raise a "killed" event when the application is
        terminated.

        If a signal handler already existed, it will be executed first,
        before the "killed" event is raised.

        Arguments:
            signals -- A list of signal names to be monitored.
                       Defaults to ['SIGHUP', 'SIGTERM'].
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
            spawning the "killed" event.
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
        """
        Generate and return a new stream ID in hexadecimal form.

        Many stanzas, handlers, or matchers may require unique
        ID values. Using this method ensures that all new ID values
        are unique in this stream.
        """
        with self._id_lock:
            self._id += 1
            return self.get_id()

    def get_id(self):
        """
        Return the current unique stream ID in hexadecimal form.
        """
        return "%X" % self._id

    def connect(self, host='', port=0, use_ssl=False,
                use_tls=True, reattempt=True):
        """
        Create a new socket and connect to the server.

        Setting reattempt to True will cause connection attempts to be made
        every second until a successful connection is established.

        Arguments:
            host      -- The name of the desired server for the connection.
            port      -- Port to connect to on the server.
            use_ssl   -- Flag indicating if SSL should be used.
            use_tls   -- Flag indicating if TLS should be used.
            reattempt -- Flag indicating if the socket should reconnect
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
        while reattempt and not connected:
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
            log.debug('Waiting %s seconds before connecting.' % delay)
            time.sleep(delay)

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
                log.debug("Connecting to %s:%s" % self.address)
                self.socket.connect(self.address)

            self.set_socket(self.socket, ignore=True)
            #this event is where you should set your application state
            self.event("connected", direct=True)
            self.reconnect_delay = 1.0
            return True
        except Socket.error as serr:
            error_msg = "Could not connect to %s:%s. Socket Error #%s: %s"
            self.event('socket_error', serr)
            log.error(error_msg % (self.address[0], self.address[1],
                                       serr.errno, serr.strerror))
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
            log.debug("Connecting to proxy: %s:%s" % address)
            self.socket.connect(address)
            self.send_raw(headers, now=True)
            resp = ''
            while '\r\n\r\n' not in resp:
                resp += self.socket.recv(1024).decode('utf-8')
            log.debug('RECV: %s' % resp)

            lines = resp.split('\r\n')
            if '200' not in lines[0]:
                self.event('proxy_error', resp)
                log.error('Proxy Error: %s' % lines[0])
                return False

            # Proxy connection established, continue connecting
            # with the XMPP server.
            return True
        except Socket.error as serr:
            error_msg = "Could not connect to %s:%s. Socket Error #%s: %s"
            self.event('socket_error', serr)
            log.error(error_msg % (self.address[0], self.address[1],
                                       serr.errno, serr.strerror))
            return False

    def _handle_connected(self, event=None):
        """
        Add check to ensure that a session is established within
        a reasonable amount of time.
        """

        def _handle_session_timeout():
            if not self.session_started_event.isSet():
                log.debug("Session start has taken more " + \
                          "than %d seconds" % self.session_timeout)
                self.disconnect(reconnect=self.auto_reconnect)

        self.schedule("Session timeout check",
                self.session_timeout,
                _handle_session_timeout)


    def disconnect(self, reconnect=False, wait=False):
        """
        Terminate processing and close the XML streams.

        Optionally, the connection may be reconnected and
        resume processing afterwards.

        If the disconnect should take place after all items
        in the send queue have been sent, use wait=True. However,
        take note: If you are constantly adding items to the queue
        such that it is never empty, then the disconnect will
        not occur and the call will continue to block.

        Arguments:
            reconnect -- Flag indicating if the connection
                         and processing should be restarted.
                         Defaults to False.
            wait      -- Flag indicating if the send queue should
                         be emptied before disconnecting.
        """
        self.state.transition('connected', 'disconnected', wait=0.0,
                              func=self._disconnect, args=(reconnect, wait))

    def _disconnect(self, reconnect=False, wait=False):
        # Wait for the send queue to empty.
        if wait:
            self.send_queue.join()

        # Send the end of stream marker.
        self.send_raw(self.stream_footer, now=True)
        self.session_started_event.clear()
        # Wait for confirmation that the stream was
        # closed in the other direction.
        self.auto_reconnect = reconnect
        log.debug('Waiting for %s from server' % self.stream_footer)
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
            self.event('session_end', direct=True)
            self.event("disconnected", direct=True)
            return True

    def reconnect(self):
        """
        Reset the stream's state and reconnect to the server.
        """
        log.debug("reconnecting...")
        self.state.transition('connected', 'disconnected', wait=2.0,
                              func=self._disconnect, args=(True,))
        log.debug("connecting...")
        return self.state.transition('disconnected', 'connected',
                                     wait=2.0, func=self._connect)

    def set_socket(self, socket, ignore=False):
        """
        Set the socket to use for the stream.

        The filesocket will be recreated as well.

        Arguments:
            socket -- The new socket to use.
            ignore -- don't set the state
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
        """
        Set timeout and other options for self.socket.

        Meant to be overridden.
        """
        self.socket.settimeout(None)

    def configure_dns(self, resolver, domain=None, port=None):
        """
        Configure and set options for a dns.resolver.Resolver
        instance, and other DNS related tasks. For example, you
        can also check Socket.getaddrinfo to see if you need to
        call out to libresolv.so.2 to run res_init().

        Meant to be overridden.

        Arguments:
            resolver -- A dns.resolver.Resolver instance, or None
                        if dnspython is not installed.
            domain   -- The initial domain under consideration.
            port     -- The initial port under consideration.
        """
        pass

    def start_tls(self):
        """
        Perform handshakes for TLS.

        If the handshake is successful, the XML stream will need
        to be restarted.
        """
        if self.ssl_support:
            log.info("Negotiating TLS")
            log.info("Using SSL version: %s" % str(self.ssl_version))
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
        """
        Begin sending whitespace periodically to keep the connection alive.

        May be disabled by setting:
            self.whitespace_keepalive = False

        The keepalive interval can be set using:
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
        """
        Perform any initialization actions, such as handshakes, once the
        stream header has been sent.

        Meant to be overridden.
        """
        pass

    def register_stanza(self, stanza_class):
        """
        Add a stanza object class as a known root stanza. A root stanza is
        one that appears as a direct child of the stream's root element.

        Stanzas that appear as substanzas of a root stanza do not need to
        be registered here. That is done using register_stanza_plugin() from
        sleekxmpp.xmlstream.stanzabase.

        Stanzas that are not registered will not be converted into
        stanza objects, but may still be processed using handlers and
        matchers.

        Arguments:
            stanza_class -- The top-level stanza object's class.
        """
        self.__root_stanza.append(stanza_class)

    def remove_stanza(self, stanza_class):
        """
        Remove a stanza from being a known root stanza. A root stanza is
        one that appears as a direct child of the stream's root element.

        Stanzas that are not registered will not be converted into
        stanza objects, but may still be processed using handlers and
        matchers.
        """
        del self.__root_stanza[stanza_class]

    def add_handler(self, mask, pointer, name=None, disposable=False,
                    threaded=False, filter=False, instream=False):
        """
        A shortcut method for registering a handler using XML masks.

        Arguments:
            mask       -- An XML snippet matching the structure of the
                          stanzas that will be passed to this handler.
            pointer    -- The handler function itself.
            name       -- A unique name for the handler. A name will
                          be generated if one is not provided.
            disposable -- Indicates if the handler should be discarded
                          after one use.
            threaded   -- Deprecated. Remains for backwards compatibility.
            filter     -- Deprecated. Remains for backwards compatibility.
            instream   -- Indicates if the handler should execute during
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
        """
        Add a stream event handler that will be executed when a matching
        stanza is received.

        Arguments:
            handler -- The handler object to execute.
        """
        if handler.stream is None:
            self.__handlers.append(handler)
            handler.stream = weakref.ref(self)

    def remove_handler(self, name):
        """
        Remove any stream event handlers with the given name.

        Arguments:
            name -- The name of the handler.
        """
        idx = 0
        for handler in self.__handlers:
            if handler.name == name:
                self.__handlers.pop(idx)
                return True
            idx += 1
        return False

    def get_dns_records(self, domain, port=None):
        """
        Get the DNS records for a domain.

        Arguments:
            domain -- The domain in question.
            port   -- If the results don't include a port, use this one.
        """
        if port is None:
            port = self.default_port
        if DNSPYTHON:
            resolver = dns.resolver.get_default_resolver()
            self.configure_dns(resolver, domain=domain, port=port)

            try:
                answers = resolver.query(domain, dns.rdatatype.A)
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                log.warning("No A records for %s" % domain)
                return [((domain, port), 0, 0)]
            except dns.exception.Timeout:
                log.warning("DNS resolution timed out " + \
                            "for A record of %s" % domain)
                return [((domain, port), 0, 0)]
            else:
                return [((ans.address, port), 0, 0) for ans in answers]
        else:
            log.warning("dnspython is not installed -- " + \
                        "relying on OS A record resolution")
            self.configure_dns(None, domain=domain, port=port)
            return [((domain, port), 0, 0)]

    def pick_dns_answer(self, domain, port=None):
        """
        Pick a server and port from DNS answers.
        Gets DNS answers if none available.
        Removes used answer from available answers.

        Arguments:
            domain -- The domain in question.
            port   -- If the results don't include a port, use this one.
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
        log.debug("Trying to connect to %s:%s" % address)
        return address

    def add_event_handler(self, name, pointer,
                          threaded=False, disposable=False):
        """
        Add a custom event handler that will be executed whenever
        its event is manually triggered.

        Arguments:
            name       -- The name of the event that will trigger
                          this handler.
            pointer    -- The function to execute.
            threaded   -- If set to True, the handler will execute
                          in its own thread. Defaults to False.
            disposable -- If set to True, the handler will be
                          discarded after one use. Defaults to False.
        """
        if not name in self.__event_handlers:
            self.__event_handlers[name] = []
        self.__event_handlers[name].append((pointer, threaded, disposable))

    def del_event_handler(self, name, pointer):
        """
        Remove a function as a handler for an event.

        Arguments:
            name    -- The name of the event.
            pointer -- The function to remove as a handler.
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
        """
        Indicates if an event has any associated handlers.

        Returns the number of registered handlers.

        Arguments:
            name -- The name of the event to check.
        """
        return len(self.__event_handlers.get(name, []))

    def event(self, name, data={}, direct=False):
        """
        Manually trigger a custom event.

        Arguments:
            name     -- The name of the event to trigger.
            data     -- Data that will be passed to each event handler.
                        Defaults to an empty dictionary.
            direct   -- Runs the event directly if True, skipping the
                        event queue. All event handlers will run in the
                        same thread.
        """
        for handler in self.__event_handlers.get(name, []):
            if direct:
                try:
                    handler[0](copy.copy(data))
                except Exception as e:
                    error_msg = 'Error processing event handler: %s'
                    log.exception(error_msg % str(handler[0]))
                    if hasattr(data, 'exception'):
                        data.exception(e)
                    else:
                        self.exception(e)
            else:
                self.event_queue.put(('event', handler, copy.copy(data)))

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
        """
        Schedule a callback function to execute after a given delay.

        Arguments:
            name     -- A unique name for the scheduled callback.
            seconds  -- The time in seconds to wait before executing.
            callback -- A pointer to the function to execute.
            args     -- A tuple of arguments to pass to the function.
            kwargs   -- A dictionary of keyword arguments to pass to
                        the function.
            repeat   -- Flag indicating if the scheduled event should
                        be reset and repeat after executing.
        """
        self.scheduler.add(name, seconds, callback, args, kwargs,
                           repeat, qpointer=self.event_queue)

    def incoming_filter(self, xml):
        """
        Filter incoming XML objects before they are processed.

        Possible uses include remapping namespaces, or correcting elements
        from sources with incorrect behavior.

        Meant to be overridden.
        """
        return xml

    def send(self, data, mask=None, timeout=None, now=False):
        """
        A wrapper for send_raw for sending stanza objects.

        May optionally block until an expected response is received.

        Arguments:
            data    -- The stanza object to send on the stream.
            mask    -- Deprecated. An XML snippet matching the structure
                       of the expected response. Execution will block
                       in this thread until the response is received
                       or a timeout occurs.
            timeout -- Time in seconds to wait for a response before
                       continuing. Defaults to RESPONSE_TIMEOUT.
            now     -- Indicates if the send queue should be skipped,
                       sending the stanza immediately. Useful mainly
                       for stream initialization stanzas.
                       Defaults to False.
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
        """
        Send an XML object on the stream, and optionally wait
        for a response.

        Arguments:
            data    -- The XML object to send on the stream.
            mask    -- Deprecated. An XML snippet matching the structure
                       of the expected response. Execution will block
                       in this thread until the response is received
                       or a timeout occurs.
            timeout -- Time in seconds to wait for a response before
                       continuing. Defaults to RESPONSE_TIMEOUT.
            now     -- Indicates if the send queue should be skipped,
                       sending the stanza immediately. Useful mainly
                       for stream initialization stanzas.
                       Defaults to False.
        """
        if timeout is None:
            timeout = self.response_timeout
        return self.send(tostring(data), mask, timeout, now)

    def send_raw(self, data, now=False, reconnect=None):
        """
        Send raw data across the stream.

        Arguments:
            data      -- Any string value.
            reconnect -- Indicates if the stream should be
                         restarted if there is an error sending
                         the stanza. Used mainly for testing.
                         Defaults to self.auto_reconnect.
        """
        if now:
            log.debug("SEND (IMMED): %s" % data)
            try:
                data = data.encode('utf-8')
                total = len(data)
                sent = 0
                count = 0
                while sent < total and not self.stop.is_set():
                    sent += self.socket.send(data[sent:])
                    count += 1
                if count > 1:
                    log.debug('SENT: %d chunks' % count)
            except Socket.error as serr:
                self.event('socket_error', serr)
                log.warning("Failed to send %s" % data)
                if reconnect is None:
                    reconnect = self.auto_reconnect
                self.disconnect(reconnect)
        else:
            self.send_queue.put(data)
        return True

    def process(self, **kwargs):
        """
        Initialize the XML streams and begin processing events.

        The number of threads used for processing stream events is determined
        by HANDLER_THREADS.

        Arguments:
            block -- If block=False then event dispatcher will run
                     in a separate thread, allowing for the stream to be
                     used in the background for another application.
                     Otherwise, process(block=True) blocks the current thread.
                     Defaults to False.

            **threaded is deprecated and included for API compatibility**
            threaded -- If threaded=True then event dispatcher will run
                        in a separate thread, allowing for the stream to be
                        used in the background for another application.
                        Defaults to True.

            Event handlers and the send queue will be threaded
            regardless of these parameters.
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
            self.__thread[name].daemon = True
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
        """
        Start processing the XML streams.

        Processing will continue after any recoverable errors
        if reconnections are allowed.
        """

        # The body of this loop will only execute once per connection.
        # Additional passes will be made only if an error occurs and
        # reconnecting is permitted.
        while True:
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
            except SyntaxError as e:
                log.error("Error reading from XML stream.")
                self.exception(e)
            except KeyboardInterrupt:
                log.debug("Keyboard Escape Detected in _process")
                self.stop.set()
            except SystemExit:
                log.debug("SystemExit in _process")
                self.stop.set()
                self.scheduler.quit()
            except Socket.error as serr:
                self.event('socket_error', serr)
                log.exception('Socket Error')
            except:
                if not self.stop.is_set():
                    log.exception('Connection error.')

            if not self.stop.is_set():
                if self.auto_reconnect:
                    self.reconnect()
                else:
                    continue
            else:
                self.disconnect()
                break

    def __read_xml(self):
        """
        Parse the incoming XML stream, raising stream events for
        each received stanza.
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
        """
        Create a stanza object from a given XML object.

        If a specialized stanza type is not found for the XML, then
        a generic StanzaBase stanza will be returned.

        Arguments:
            xml        -- The XML object to convert into a stanza object.
            default_ns -- Optional default namespace to use instead of the
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

        Arguments:
            xml -- The XML stanza to analyze.
        """
        log.debug("RECV: %s" % tostring(xml,
                                            xmlns=self.default_ns,
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
        for handler in self.__handlers:
            if handler.match(stanza):
                stanza_copy = copy.copy(stanza)
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
        """
        Capture exceptions for event handlers that run
        in individual threads.

        Arguments:
            func -- The event handler to execute.
            args -- Arguments to the event handler.
        """
        orig = copy.copy(args[0])
        try:
            func(*args)
        except Exception as e:
            error_msg = 'Error processing event handler: %s'
            log.exception(error_msg % str(func))
            if hasattr(orig, 'exception'):
                orig.exception(e)
            else:
                self.exception(e)

    def _event_runner(self):
        """
        Process the event queue and execute handlers.

        The number of event runner threads is controlled by HANDLER_THREADS.

        Stream event handlers will all execute in this thread. Custom event
        handlers may be spawned in individual threads.
        """
        log.debug("Loading event runner")
        try:
            while not self.stop.isSet():
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
                        log.exception(error_msg % handler.name)
                        orig.exception(e)
                elif etype == 'schedule':
                    name = args[1]
                    try:
                        log.debug('Scheduled event: %s: %s' % (name, args[0]))
                        handler(*args[0])
                    except Exception as e:
                        log.exception('Error processing scheduled task')
                        self.exception(e)
                elif etype == 'event':
                    func, threaded, disposable = handler
                    orig = copy.copy(args[0])
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
                        log.exception(error_msg % str(func))
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
        """
        Extract stanzas from the send queue and send them on the stream.
        """
        try:
            while not self.stop.is_set():
                self.session_started_event.wait()
                if self.__failed_send_stanza is not None:
                    data = self.__failed_send_stanza
                    self.__failed_send_stanza = None
                else:
                    try:
                        data = self.send_queue.get(True, 1)
                    except queue.Empty:
                        continue
                log.debug("SEND: %s" % data)
                try:
                    enc_data = data.encode('utf-8')
                    total = len(enc_data)
                    sent = 0
                    count = 0
                    while sent < total and not self.stop.is_set():
                        sent += self.socket.send(enc_data[sent:])
                        count += 1
                    if count > 1:
                        log.debug('SENT: %d chunks' % count)
                    self.send_queue.task_done()
                except Socket.error as serr:
                    self.event('socket_error', serr)
                    log.warning("Failed to send %s" % data)
                    self.__failed_send_stanza = data
                    self.disconnect(self.auto_reconnect)
        except Exception as ex:
            log.exception('Unexpected error in send thread: %s' % ex)
            self.exception(ex)
            if not self.stop.is_set():
                self.disconnect(self.auto_reconnect)

    def exception(self, exception):
        """
        Process an unknown exception.

        Meant to be overridden.

        Arguments:
            exception -- An unhandled exception object.
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
