"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from __future__ import with_statement, unicode_literals

import copy
import logging
import socket
import ssl
import sys
import threading
import time
import types
try:
    import queue
except ImportError:
    import Queue as queue

from sleekxmpp.xmlstream import StateMachine, Scheduler, tostring
from sleekxmpp.xmlstream.stanzabase import StanzaBase, ET

# In Python 2.x, file socket objects are broken. A patched socket
# wrapper is provided for this case in filesocket.py.
if sys.version_info < (3, 0):
    from sleekxmpp.xmlstream.filesocket import FileSocket, Socket26


# The time in seconds to wait before timing out waiting for response stanzas.
RESPONSE_TIMEOUT = 10

# The number of threads to use to handle XML stream events. This is not the
# same as the number of custom event handling threads. HANDLER_THREADS must
# be at least 1.
HANDLER_THREADS = 1

# Flag indicating if the SSL library is available for use.
SSL_SUPPORT = True


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
        namespace_map -- Optional mapping of namespaces to namespace prefixes.
        scheduler     -- A scheduler object for triggering events
                         after a given period of time.
        send_queue    -- A queue of stanzas to be sent on the stream.
        socket        -- The connection to the server.
        ssl_support   -- Indicates if a SSL library is available for use.
        state         -- A state machine for managing the stream's
                         connection state.
        stream_footer -- The start tag and any attributes for the stream's
                         root element.
        stream_header -- The closing tag of the stream's root element.
        use_ssl       -- Flag indicating if SSL should be used.
        use_tls       -- Flag indicating if TLS should be used.

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
        # To comply with PEP8, method names now use underscores.
        # Deprecated method names are re-mapped for backwards compatibility.
        self.startTLS = self.start_tls
        self.registerStanza = self.register_stanza
        self.removeStanza = self.remove_stanza
        self.registerHandler = self.register_handler
        self.removeHandler = self.remove_handler
        self.setSocket = self.set_socket
        self.sendRaw = self.send_raw
        self.getId = self.get_id
        self.getNewId = self.new_id
        self.sendXML = self.send_xml

        self.ssl_support = SSL_SUPPORT

        # TODO: Integrate the new state machine.
        self.state = StateMachine()
        self.state.addStates({'connected': False,
                              'is client': False,
                              'ssl': False,
                              'tls': False,
                              'reconnect': True,
                              'processing': False,
                              'disconnecting': False})

        self.address = (host, int(port))
        self.filesocket = None
        self.set_socket(socket)

        self.use_ssl = False
        self.use_tls = False

        self.default_ns = ''
        self.stream_header = "<stream>"
        self.stream_footer = "</stream>"

        self.event_queue = queue.Queue()
        self.send_queue = queue.Queue()
        self.scheduler = Scheduler(self.event_queue)

        self.namespace_map = {}

        self.__thread = {}
        self.__root_stanza = []
        self.__handlers = []

        self._id = 0
        self._id_lock = threading.Lock()

        self.run = True

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

        # Respect previous SSL and TLS usage directives.
        if use_ssl is not None:
            self.use_ssl = use_ssl
        if use_tls is not None:
            self.use_tls = use_tls

        self.state.set('is client', True)

        # Repeatedly attempt to connect until a successful connection
        # is established.
        while reattempt and not self.state['connected']:
            if sys.version_info < (3, 0):
                self.socket = Socket26(socket.AF_INET, socket.SOCK_STREAM)
            else:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(None)
            if self.use_ssl and self.ssl_support:
                logging.debug("Socket Wrapped for SSL")
                self.socket = ssl.wrap_socket(self.socket)

            try:
                self.socket.connect(self.address)
                self.set_socket(self.socket)
                self.state.set('connected', True)
                return True
            except socket.error as serr:
                error_msg = "Could not connect. Socket Error #%s: %s"
                logging.error(error_msg % (serr.errno, serr.strerror))
                time.sleep(1)

    def disconnect(self, reconnect=False):
        """
        Terminate processing and close the XML streams.

        Optionally, the connection may be reconnected and
        resume processing afterwards.

        Arguments:
            reconnect -- Flag indicating if the connection
                         and processing should be restarted.
                         Defaults to False.
        """
        self.state.set('reconnect', reconnect)
        if self.state['disconnecting']:
            return
        if not self.state['reconnect']:
            logging.debug("Disconnecting...")
            self.state.set('disconnecting', True)
            self.run = False
            self.scheduler.run = False
        if self.state['connected']:
            # Send the end of stream marker.
            self.send_raw(self.stream_footer)
            # Wait for confirmation that the stream was
            # closed in the other direction.
            time.sleep(1)
        try:
            self.socket.close()
            self.filesocket.close()
            self.socket.shutdown(socket.SHUT_RDWR)
        except socket.error as serr:
            pass

    def reconnect(self):
        """
        Reset the stream's state and reconnect to the server.
        """
        self.state.set('tls', False)
        self.state.set('ssl', False)
        time.sleep(1)
        self.connect()

    def set_socket(self, socket):
        """
        Set the socket to use for the stream.

        The filesocket will be recreated as well.

        Arguments:
            socket -- The new socket to use.
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
            self.state.set('connected', True)

    def start_tls(self):
        """
        Perform handshakes for TLS.

        If the handshake is successful, the XML stream will need
        to be restarted.
        """
        if self.ssl_support:
            logging.info("Negotiating TLS")
            self.socket = ssl.wrap_socket(self.socket,
                                          ssl_version=ssl.PROTOCOL_TLSv1,
                                          do_handshake_on_connect=False)
            self.socket.do_handshake()
            self.set_socket(self.socket)
            return True
        else:
            logging.warning("Tried to enable TLS, but ssl module not found.")
            return False

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
        be registered here. That is done using registerStanzaPlugin() from
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
            handler.stream = self

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

    def send(self, data, mask, timeout=RESPONSE_TIMEOUT):
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
        """
        if hasattr(mask, 'xml'):
            mask = mask.xml
        data = str(data)
        if mask is not None:
            logging.warning("Use of send mask waiters is deprecated.")
            wait_for = Waiter("SendWait_%s" % self.new_id(), 
                              MatchXMLMask(mask))
            self.register_handler(wait_for)
        self.send_raw(data)
        if mask is not None:
            return wait_for.wait(timeout)

    def send_raw(self, data):
        """
        Send raw data across the stream.

        Arguments:
            data -- Any string value.
        """
        self.send_queue.put(data)
        return True

    def send_xml(self, data, mask=None, timeout=RESPONSE_TIMEOUT):
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
        """
        return self.send(tostring(data), mask, timeout)

    def process(self, threaded=True):
        """
        Initialize the XML streams and begin processing events.

        The number of threads used for processing stream events is determined
        by HANDLER_THREADS.

        Arguments:
            threaded -- If threaded=True then event dispatcher will run
                        in a separate thread, allowing for the stream to be
                        used in the background for another application.
                        Defaults to True.

                        Event handlers and the send queue will be threaded
                        regardless of this parameter's value.
        """
        self.scheduler.process(threaded=True)

        def start_thread(name, target):
            self.__thread[name] = threading.Thread(name=name, target=target)
            self.__thread[name].start()

        for t in range(0, HANDLER_THREADS):
            logging.debug("Starting HANDLER THREAD")
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
        firstrun = True

        # The body of this loop will only execute once per connection.
        # Additional passes will be made only if an error occurs and
        # reconnecting is permitted.
        while self.run and (firstrun or self.state['reconnect']):
            self.state.set('processing', True)
            firstrun = False
            try:
                if self.state['is client']:
                    self.send_raw(self.stream_header)
                # The call to self.__read_xml will block and prevent
                # the body of the loop from running until a disconnect
                # occurs. After any reconnection, the stream header will
                # be resent and processing will resume.
                while self.run and self.__read_xml():
                    # Ensure the stream header is sent for any
                    # new connections.
                    if self.state['is client']:
                        self.send_raw(self.stream_header)
            except KeyboardInterrupt:
                logging.debug("Keyboard Escape Detected")
                self.state.set('processing', False)
                self.state.set('reconnect', False)
                self.disconnect()
                self.run = False
                self.scheduler.run = False
                self.event_queue.put(('quit', None, None))
                return
            except SystemExit:
                self.event_queue.put(('quit', None, None))
                return
            except socket.error:
                if not self.state.reconnect:
                    return
                self.state.set('processing', False)
                logging.exception('Socket Error')
                self.disconnect(reconnect=True)
            except:
                if not self.state.reconnect:
                    return
                self.state.set('processing', False)
                logging.exception('Connection error. Reconnecting.')
                self.disconnect(reconnect=True)
            if self.state['reconnect']:
                self.reconnect()
            self.state.set('processing', False)
            self.event_queue.put(('quit', None, None))

    def __read_xml(self):
        """
        Parse the incoming XML stream, raising stream events for
        each received stanza.
        """
        depth = 0
        root = None
        for (event, xml) in ET.iterparse(self.filesocket, (b'end', b'start')):
            if event == b'start':
                if depth == 0:
                    # We have received the start of the root element.
                    root = xml
                    # Perform any stream initialization actions, such
                    # as handshakes.
                    self.start_stream_handler(root)
                depth += 1
            if event == b'end':
                depth -= 1
                if depth == 0:
                    # The stream's root element has closed,
                    # terminating the stream.
                    self.disconnect(reconnect=self.state['reconnect'])
                    logging.debug("Ending read XML loop")
                    return False
                elif depth == 1:
                    # We only raise events for stanzas that are direct
                    # children of the root element.
                    try:
                        self.__spawn_event(xml)
                    except RestartStream:
                        return True
                    if root:
                        # Keep the root element empty of children to
                        # save on memory use.
                        root.clear()
        logging.debug("Ending read XML loop")

    def __spawn_event(self, xml):
        """
        Analyze incoming XML stanzas and convert them into stanza
        objects if applicable and queue stream events to be processed
        by matching handlers.

        Arguments:
            xml -- The XML stanza to analyze.
        """
        logging.debug("RECV: %s" % tostring(xml,
                                            xmlns=self.default_ns,
                                            stream=self))
        # Apply any preprocessing filters.
        xml = self.incoming_filter(xml)

        # Convert the raw XML object into a stanza object. If no registered
        # stanza type applies, a generic StanzaBase stanza will be used.
        stanza_type = StanzaBase
        for stanza_class in self.__root_stanza:
            if xml.tag == "{%s}%s" % (self.default_ns, stanza_class.name):
                stanza_type = stanza_class
                break
        stanza = stanza_type(self, xml)

        # Match the stanza against registered handlers. Handlers marked
        # to run "in stream" will be executed immediately; the rest will
        # be queued.
        unhandled = True
        for handler in self.__handlers:
            if handler.match(stanza):
                stanza_copy = stanza_type(self, copy.deepcopy(xml))
                handler.prerun(stanza_copy)
                self.event_queue.put(('stanza', handler, stanza_copy))
                if handler.checkDelete():
                    self.__handlers.pop(self.__handlers.index(handler))
                unhandled = False

        # Some stanzas require responses, such as Iq queries. A default
        # handler will be executed immediately for this case.
        if unhandled:
            stanza.unhandled()

    def _event_runner(self):
        """
        Process the event queue and execute handlers.

        The number of event runner threads is controlled by HANDLER_THREADS.

        Stream event handlers will all execute in this thread. Custom event
        handlers may be spawned in individual threads.
        """
        logging.debug("Loading event runner")
        while self.run:
            try:
                event = self.event_queue.get(True, timeout=5)
            except queue.Empty:
                event = None
            except KeyboardInterrupt:
                self.run = False
                self.scheduler.run = False
            if event is None:
                continue

            etype, handler = event[0:2]
            args = event[2:]

            if etype == 'stanza':
                try:
                    handler.run(args[0])
                except Exception as e:
                    error_msg = 'Error processing event handler: %s'
                    logging.exception(error_msg % handler.name)
                    args[0].exception(e)
            elif etype == 'schedule':
                try:
                    logging.debug(args)
                    handler(*args[0])
                except:
                    logging.exception('Error processing scheduled task')
            elif etype == 'quit':
                logging.debug("Quitting event runner thread")
                return False

    def _send_thread(self):
        """
        Extract stanzas from the send queue and send them on the stream.
        """
        while self.run:
            data = self.send_queue.get(True)
            logging.debug("SEND: %s" % data)
            try:
                self.socket.send(data.encode('utf-8'))
            except:
                logging.warning("Failed to send %s" % data)
                self.state.set('connected', False)
                if self.state.reconnect:
                    logging.exception("Disconnected. Socket Error.")
                    self.disconnect(reconnect=True)
