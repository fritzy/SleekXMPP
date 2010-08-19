"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import unittest
import socket
try:
    import queue
except ImportError:
    import Queue as queue

import sleekxmpp
from sleekxmpp import ClientXMPP
from sleekxmpp.stanza import Message, Iq, Presence
from sleekxmpp.xmlstream.stanzabase import registerStanzaPlugin, ET
from sleekxmpp.xmlstream.tostring import tostring


class TestSocket(object):

    """
    A dummy socket that reads and writes to queues instead
    of an actual networking socket.

    Methods:
        nextSent -- Return the next sent stanza.
        recvData -- Make a stanza available to read next.
        recv     -- Read the next stanza from the socket.
        send     -- Write a stanza to the socket.
        makefile -- Dummy call, returns self.
        read     -- Read the next stanza from the socket.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a new test socket.

        Arguments:
            Same as arguments for socket.socket
        """
        self.socket = socket.socket(*args, **kwargs)
        self.recv_queue = queue.Queue()
        self.send_queue = queue.Queue()

    def __getattr__(self, name):
        """
        Return attribute values of internal, dummy socket.

        Some attributes and methods are disabled to prevent the
        socket from connecting to the network.

        Arguments:
            name -- Name of the attribute requested.
        """

        def dummy(*args):
            """Method to do nothing and prevent actual socket connections."""
            return None

        overrides = {'connect': dummy,
                     'close': dummy,
                     'shutdown': dummy}

        return overrides.get(name, getattr(self.socket, name))

    # ------------------------------------------------------------------
    # Testing Interface

    def nextSent(self, timeout=None):
        """
        Get the next stanza that has been 'sent'.

        Arguments:
            timeout -- Optional timeout for waiting for a new value.
        """
        args = {'block': False}
        if timeout is not None:
            args = {'block': True, 'timeout': timeout}
        try:
            return self.send_queue.get(**args)
        except:
            return None

    def recvData(self, data):
        """
        Add data to the receiving queue.

        Arguments:
            data -- String data to 'write' to the socket to be received
                    by the XMPP client.
        """
        self.recv_queue.put(data)

    # ------------------------------------------------------------------
    # Socket Interface

    def recv(self, *args, **kwargs):
        """
        Read a value from the received queue.

        Arguments:
            Placeholders. Same as for socket.Socket.recv.
        """
        return self.read(block=True)

    def send(self, data):
        """
        Send data by placing it in the send queue.

        Arguments:
            data -- String value to write.
        """
        self.send_queue.put(data)

    # ------------------------------------------------------------------
    # File Socket

    def makefile(self, *args, **kwargs):
        """
        File socket version to use with ElementTree.

        Arguments:
            Placeholders, same as socket.Socket.makefile()
        """
        return self

    def read(self, block=True, timeout=None, **kwargs):
        """
        Implement the file socket interface.

        Arguments:
            block   -- Indicate if the read should block until a
                       value is ready.
            timeout -- Time in seconds a block should last before
                       returning None.
        """
        if timeout is not None:
            block = True
        try:
            return self.recv_queue.get(block, timeout)
        except:
            return None


class SleekTest(unittest.TestCase):

    """
    A SleekXMPP specific TestCase class that provides
    methods for comparing message, iq, and presence stanzas.

    Methods:
        Message            -- Create a Message stanza object.
        Iq                 -- Create an Iq stanza object.
        Presence           -- Create a Presence stanza object.
        checkMessage       -- Compare a Message stanza against an XML string.
        checkIq            -- Compare an Iq stanza against an XML string.
        checkPresence      -- Compare a Presence stanza against an XML string.
        streamStart        -- Initialize a dummy XMPP client.
        streamRecv         -- Queue data for XMPP client to receive.
        streamSendMessage  -- Check that the XMPP client sent the given
                              Message stanza.
        streamSendIq       -- Check that the XMPP client sent the given
                              Iq stanza.
        streamSendPresence -- Check taht the XMPP client sent the given
                              Presence stanza.
        streamClose        -- Disconnect the XMPP client.
        fix_namespaces     -- Add top-level namespace to an XML object.
        compare            -- Compare XML objects against each other.
    """

    # ------------------------------------------------------------------
    # Shortcut methods for creating stanza objects

    def Message(self, *args, **kwargs):
        """
        Create a Message stanza.

        Uses same arguments as StanzaBase.__init__

        Arguments:
            xml -- An XML object to use for the Message's values.
        """
        return Message(None, *args, **kwargs)

    def Iq(self, *args, **kwargs):
        """
        Create an Iq stanza.

        Uses same arguments as StanzaBase.__init__

        Arguments:
            xml -- An XML object to use for the Iq's values.
        """
        return Iq(None, *args, **kwargs)

    def Presence(self, *args, **kwargs):
        """
        Create a Presence stanza.

        Uses same arguments as StanzaBase.__init__

        Arguments:
            xml -- An XML object to use for the Iq's values.
        """
        return Presence(None, *args, **kwargs)

    # ------------------------------------------------------------------
    # Methods for comparing stanza objects to XML strings

    def checkStanza(self, stanza_class, stanza, xml_string,
        defaults=None, use_values=True):
        """
        Create and compare several stanza objects to a correct XML string.

        If use_values is False, test using getStanzaValues() and
        setStanzaValues() will not be used.

        Some stanzas provide default values for some interfaces, but
        these defaults can be problematic for testing since they can easily
        be forgotten when supplying the XML string. A list of interfaces that
        use defaults may be provided and the generated stanzas will use the
        default values for those interfaces if needed.

        However, correcting the supplied XML is not possible for interfaces
        that add or remove XML elements. Only interfaces that map to XML
        attributes may be set using the defaults parameter. The supplied XML
        must take into account any extra elements that are included by default.

        Arguments:
            stanza_class -- The class of the stanza being tested.
            stanza       -- The stanza object to test.
            xml_string   -- A string version of the correct XML expected.
            defaults     -- A list of stanza interfaces that have default
                            values. These interfaces will be set to their
                            defaults for the given and generated stanzas to
                            prevent unexpected test failures.
            use_values   -- Indicates if testing using getStanzaValues() and
                            setStanzaValues() should be used. Defaults to
                            True.
        """
        xml = ET.fromstring(xml_string)

        # Ensure that top level namespaces are used, even if they
        # were not provided.
        self.fix_namespaces(stanza.xml, 'jabber:client')
        self.fix_namespaces(xml, 'jabber:client')

        stanza2 = stanza_class(xml=xml)

        if use_values:
            # Using getStanzaValues() and setStanzaValues() will add
            # XML for any interface that has a default value. We need
            # to set those defaults on the existing stanzas and XML
            # so that they will compare correctly.
            default_stanza = stanza_class()
            if defaults is None:
                defaults = []
            for interface in defaults:
                stanza[interface] = stanza[interface]
                stanza2[interface] = stanza2[interface]
                # Can really only automatically add defaults for top
                # level attribute values. Anything else must be accounted
                # for in the provided XML string.
                if interface not in xml.attrib:
                    if interface in default_stanza.xml.attrib:
                        value = default_stanza.xml.attrib[interface]
                        xml.attrib[interface] = value

            values = stanza2.getStanzaValues()
            stanza3 = stanza_class()
            stanza3.setStanzaValues(values)

            debug = "Three methods for creating stanzas do not match.\n"
            debug += "Given XML:\n%s\n" % tostring(xml)
            debug += "Given stanza:\n%s\n" % tostring(stanza.xml)
            debug += "Generated stanza:\n%s\n" % tostring(stanza2.xml)
            debug += "Second generated stanza:\n%s\n" % tostring(stanza3.xml)
            result = self.compare(xml, stanza.xml, stanza2.xml, stanza3.xml)
        else:
            debug = "Two methods for creating stanzas do not match.\n"
            debug += "Given XML:\n%s\n" % tostring(xml)
            debug += "Given stanza:\n%s\n" % tostring(stanza.xml)
            debug += "Generated stanza:\n%s\n" % tostring(stanza2.xml)
            result = self.compare(xml, stanza.xml, stanza2.xml)

        self.failUnless(result, debug)

    def checkMessage(self, msg, xml_string, use_values=True):
        """
        Create and compare several message stanza objects to a
        correct XML string.

        If use_values is False, the test using getStanzaValues() and
        setStanzaValues() will not be used.

        Arguments:
            msg        -- The Message stanza object to check.
            xml_string -- The XML contents to compare against.
            use_values -- Indicates if the test using getStanzaValues
                          and setStanzaValues should be used. Defaults
                          to True.
        """

        return self.checkStanza(Message, msg, xml_string,
                                defaults=['type'],
                                use_values = use_values)

    def checkIq(self, iq, xml_string, use_values=True):
        """
        Create and compare several iq stanza objects to a
        correct XML string.

        If use_values is False, the test using getStanzaValues() and
        setStanzaValues() will not be used.

        Arguments:
            iq         -- The Iq stanza object to check.
            xml_string -- The XML contents to compare against.
            use_values -- Indicates if the test using getStanzaValues
                          and setStanzaValues should be used. Defaults
                          to True.
        """
        return self.checkStanza(Iq, iq, xml_string, use_values=use_values)

    def checkPresence(self, pres, xml_string, use_values=True):
        """
        Create and compare several presence stanza objects to a
        correct XML string.

        If use_values is False, the test using getStanzaValues() and
        setStanzaValues() will not be used.

        Arguments:
            iq         -- The Iq stanza object to check.
            xml_string -- The XML contents to compare against.
            use_values -- Indicates if the test using getStanzaValues
                          and setStanzaValues should be used. Defaults
                          to True.
        """
        return self.checkStanza(Presence, pres, xml_string,
                                defaults=['priority'],
                                use_values=use_values)

    # ------------------------------------------------------------------
    # Methods for simulating stanza streams.

    def streamStart(self, mode='client', skip=True):
        """
        Initialize an XMPP client or component using a dummy XML stream.

        Arguments:
            mode -- Either 'client' or 'component'. Defaults to 'client'.
            skip -- Indicates if the first item in the sent queue (the
                    stream header) should be removed. Tests that wish
                    to test initializing the stream should set this to
                    False. Otherwise, the default of True should be used.
        """
        if mode == 'client':
            self.xmpp = ClientXMPP('tester@localhost', 'test')
            self.xmpp.setSocket(TestSocket())

            self.xmpp.state.set('reconnect', False)
            self.xmpp.state.set('is client', True)
            self.xmpp.state.set('connected', True)

            # Must have the stream header ready for xmpp.process() to work
            self.xmpp.socket.recvData(self.xmpp.stream_header)

        self.xmpp.connectTCP = lambda a, b, c, d: True
        self.xmpp.startTLS = lambda: True
        self.xmpp.process(threaded=True)
        if skip:
            # Clear startup stanzas
            self.xmpp.socket.nextSent(timeout=0.01)

    def streamRecv(self, data):
        """
        Pass data to the dummy XMPP client as if it came from an XMPP server.

        Arguments:
            data -- String stanza XML to be received and processed by the
                    XMPP client or component.
        """
        data = str(data)
        self.xmpp.socket.recvData(data)

    def streamSendMessage(self, data, use_values=True, timeout=.1):
        """
        Check that the XMPP client sent the given stanza XML.

        Extracts the next sent stanza and compares it with the given
        XML using checkMessage.

        Arguments:
            data       -- The XML string of the expected Message stanza,
                          or an equivalent stanza object.
            use_values -- Modifies the type of tests used by checkMessage.
            timeout    -- Time in seconds to wait for a stanza before
                          failing the check.
        """
        if isinstance(data, str):
            data = self.Message(xml=ET.fromstring(data))
        sent = self.xmpp.socket.nextSent(timeout)
        self.checkMessage(data, sent, use_values)

    def streamSendIq(self, data, use_values=True, timeout=.1):
        """
        Check that the XMPP client sent the given stanza XML.

        Extracts the next sent stanza and compares it with the given
        XML using checkIq.

        Arguments:
            data       -- The XML string of the expected Iq stanza,
                          or an equivalent stanza object.
            use_values -- Modifies the type of tests used by checkIq.
            timeout    -- Time in seconds to wait for a stanza before
                          failing the check.
        """
        if isinstance(data, str):
            data = self.Iq(xml=ET.fromstring(data))
        sent = self.xmpp.socket.nextSent(timeout)
        self.checkIq(data, sent, use_values)

    def streamSendPresence(self, data, use_values=True, timeout=.1):
        """
        Check that the XMPP client sent the given stanza XML.

        Extracts the next sent stanza and compares it with the given
        XML using checkPresence.

        Arguments:
            data       -- The XML string of the expected Presence stanza,
                          or an equivalent stanza object.
            use_values -- Modifies the type of tests used by checkPresence.
            timeout    -- Time in seconds to wait for a stanza before
                          failing the check.
        """
        if isinstance(data, str):
            data = self.Presence(xml=ET.fromstring(data))
        sent = self.xmpp.socket.nextSent(timeout)
        self.checkPresence(data, sent, use_values)

    def streamClose(self):
        """
        Disconnect the dummy XMPP client.

        Can be safely called even if streamStart has not been called.

        Must be placed in the tearDown method of a test class to ensure
        that the XMPP client is disconnected after an error.
        """
        if hasattr(self, 'xmpp') and self.xmpp is not None:
            self.xmpp.disconnect()
            self.xmpp.socket.recvData(self.xmpp.stream_footer)

    # ------------------------------------------------------------------
    # XML Comparison and Cleanup

    def fix_namespaces(self, xml, ns):
        """
        Assign a namespace to an element and any children that
        don't have a namespace.

        Arguments:
            xml -- The XML object to fix.
            ns  -- The namespace to add to the XML object.
        """
        if xml.tag.startswith('{'):
            return
        xml.tag = '{%s}%s' % (ns, xml.tag)
        for child in xml.getchildren():
            self.fix_namespaces(child, ns)

    def compare(self, xml, *other):
        """
        Compare XML objects.

        Arguments:
            xml   -- The XML object to compare against.
            *other -- The list of XML objects to compare.
        """
        if not other:
            return False

        # Compare multiple objects
        if len(other) > 1:
            for xml2 in other:
                if not self.compare(xml, xml2):
                    return False
            return True

        other = other[0]

        # Step 1: Check tags
        if xml.tag != other.tag:
            return False

        # Step 2: Check attributes
        if xml.attrib != other.attrib:
            return False

        # Step 3: Recursively check children
        for child in xml:
            child2s = other.findall("%s" % child.tag)
            if child2s is None:
                return False
            for child2 in child2s:
                if self.compare(child, child2):
                    break
            else:
                return False

        # Everything matches
        return True
