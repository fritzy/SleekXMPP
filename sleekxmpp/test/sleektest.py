"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import unittest

import sleekxmpp
from sleekxmpp import ClientXMPP, ComponentXMPP
from sleekxmpp.stanza import Message, Iq, Presence
from sleekxmpp.test import TestSocket
from sleekxmpp.xmlstream.stanzabase import registerStanzaPlugin, ET
from sleekxmpp.xmlstream.tostring import tostring


class SleekTest(unittest.TestCase):

    """
    A SleekXMPP specific TestCase class that provides
    methods for comparing message, iq, and presence stanzas.

    Methods:
        Message              -- Create a Message stanza object.
        Iq                   -- Create an Iq stanza object.
        Presence             -- Create a Presence stanza object.
        check_stanza         -- Compare a generic stanza against an XML string.
        check_message        -- Compare a Message stanza against an XML string.
        check_iq             -- Compare an Iq stanza against an XML string.
        check_presence       -- Compare a Presence stanza against an XML string.
        stream_start         -- Initialize a dummy XMPP client.
        stream_recv          -- Queue data for XMPP client to receive.
        stream_make_header   -- Create a stream header.
        stream_send_header   -- Check that the given header has been sent.
        stream_send_message  -- Check that the XMPP client sent the given
                                Message stanza.
        stream_send_iq       -- Check that the XMPP client sent the given
                                Iq stanza.
        stream_send_presence -- Check thatt the XMPP client sent the given
                                Presence stanza.
        stream_send_stanza   -- Check that the XMPP client sent the given
                                generic stanza.
        stream_close         -- Disconnect the XMPP client.
        fix_namespaces       -- Add top-level namespace to an XML object.
        compare              -- Compare XML objects against each other.
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

    def check_stanza(self, stanza_class, stanza, xml_string,
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

    def check_message(self, msg, xml_string, use_values=True):
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

        return self.check_stanza(Message, msg, xml_string,
                                defaults=['type'],
                                use_values=use_values)

    def check_iq(self, iq, xml_string, use_values=True):
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
        return self.check_stanza(Iq, iq, xml_string, use_values=use_values)

    def check_presence(self, pres, xml_string, use_values=True):
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
        return self.check_stanza(Presence, pres, xml_string,
                                defaults=['priority'],
                                use_values=use_values)

    # ------------------------------------------------------------------
    # Methods for simulating stanza streams.

    def stream_start(self, mode='client', skip=True, header=None):
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
        elif mode == 'component':
            self.xmpp = ComponentXMPP('tester.localhost', 'test',
                                      'localhost', 8888)
        else:
            raise ValueError("Unknown XMPP connection mode.")

        self.xmpp.setSocket(TestSocket())
        self.xmpp.state.set('reconnect', False)
        self.xmpp.state.set('is client', True)
        self.xmpp.state.set('connected', True)

        # Must have the stream header ready for xmpp.process() to work.
        if not header:
            header = self.xmpp.stream_header
        self.xmpp.socket.recv_data(header)

        self.xmpp.connect = lambda a=None, b=None, c=None, d=None: True
        self.xmpp.process(threaded=True)
        if skip:
            # Clear startup stanzas
            self.xmpp.socket.next_sent(timeout=0.01)
            if mode == 'component':
                self.xmpp.socket.next_sent(timeout=0.01)

    def stream_recv(self, data):
        """
        Pass data to the dummy XMPP client as if it came from an XMPP server.

        Arguments:
            data -- String stanza XML to be received and processed by the
                    XMPP client or component.
        """
        data = str(data)
        self.xmpp.socket.recv_data(data)

    def stream_make_header(self, sto='',
                                 sfrom='',
                                 sid='',
                                 stream_ns="http://etherx.jabber.org/streams",
                                 default_ns="jabber:client",
                                 version="1.0",
                                 xml_header=True):
        """
        Create a stream header to be received by the test XMPP agent.

        The header must be saved and passed to stream_start.

        Arguments:
            sto        -- The recipient of the stream header.
            sfrom      -- The agent sending the stream header.
            sid        -- The stream's id.
            stream_ns  -- The namespace of the stream's root element.
            default_ns -- The default stanza namespace.
            version    -- The stream version.
            xml_header -- Indicates if the XML version header should be
                          appended before the stream header.
        """
        header = '<stream:stream %s>'
        parts = []
        if xml_header:
            header = '<?xml version="1.0"?>' + header
        if sto:
            parts.append('to="%s"' % sto)
        if sfrom:
            parts.append('from="%s"' % sfrom)
        if sid:
            parts.append('id="%s"' % sid)
        parts.append('version="%s"' % version)
        parts.append('xmlns:stream="%s"' % stream_ns)
        parts.append('xmlns="%s"' % default_ns)
        return header % ' '.join(parts)

    def stream_send_header(self, sto='',
                                 sfrom='',
                                 sid='',
                                 stream_ns="http://etherx.jabber.org/streams",
                                 default_ns="jabber:client",
                                 version="1.0",
                                 xml_header=False,
                                 timeout=0.1):
        """
        Check that a given stream header was sent.

        Arguments:
            sto        -- The recipient of the stream header.
            sfrom      -- The agent sending the stream header.
            sid        -- The stream's id.
            stream_ns  -- The namespace of the stream's root element.
            default_ns -- The default stanza namespace.
            version    -- The stream version.
            xml_header -- Indicates if the XML version header should be
                          appended before the stream header.
            timeout    -- Length of time to wait in seconds for a
                          response.
        """
        header = self.stream_make_header(sto, sfrom, sid,
                                         stream_ns=stream_ns,
                                         default_ns=default_ns,
                                         version=version,
                                         xml_header=xml_header)
        sent_header = self.xmpp.socket.next_sent(timeout)
        if sent_header is None:
            raise ValueError("Socket did not return data.")

        # Apply closing elements so that we can construct
        # XML objects for comparison.
        header2 = header + '</stream:stream>'
        sent_header2 = sent_header + '</stream:stream>'

        xml = ET.fromstring(header2)
        sent_xml = ET.fromstring(sent_header2)

        self.failUnless(
            self.compare(xml, sent_xml),
            "Stream headers do not match:\nDesired:\n%s\nSent:\n%s" % (
                header, sent_header))

    def stream_send_stanza(self, stanza_class, data, defaults=None,
                           use_values=True, timeout=.1):
        """
        Check that the XMPP client sent the given stanza XML.

        Extracts the next sent stanza and compares it with the given
        XML using check_stanza.

        Arguments:
            stanza_class -- The class of the sent stanza object.
            data         -- The XML string of the expected Message stanza,
                            or an equivalent stanza object.
            use_values   -- Modifies the type of tests used by check_message.
            defaults     -- A list of stanza interfaces that have defaults
                            values which may interfere with comparisons.
            timeout      -- Time in seconds to wait for a stanza before
                            failing the check.
        """
        if isintance(data, str):
            data = stanza_class(xml=ET.fromstring(data))
        sent = self.xmpp.socket.next_sent(timeout)
        self.check_stanza(stanza_class, data, sent,
                          defaults=defaults,
                          use_values=use_values)

    def stream_send_message(self, data, use_values=True, timeout=.1):
        """
        Check that the XMPP client sent the given stanza XML.

        Extracts the next sent stanza and compares it with the given
        XML using check_message.

        Arguments:
            data       -- The XML string of the expected Message stanza,
                          or an equivalent stanza object.
            use_values -- Modifies the type of tests used by check_message.
            timeout    -- Time in seconds to wait for a stanza before
                          failing the check.
        """
        if isinstance(data, str):
            data = self.Message(xml=ET.fromstring(data))
        sent = self.xmpp.socket.next_sent(timeout)
        self.check_message(data, sent, use_values)

    def stream_send_iq(self, data, use_values=True, timeout=.1):
        """
        Check that the XMPP client sent the given stanza XML.

        Extracts the next sent stanza and compares it with the given
        XML using check_iq.

        Arguments:
            data       -- The XML string of the expected Iq stanza,
                          or an equivalent stanza object.
            use_values -- Modifies the type of tests used by check_iq.
            timeout    -- Time in seconds to wait for a stanza before
                          failing the check.
        """
        if isinstance(data, str):
            data = self.Iq(xml=ET.fromstring(data))
        sent = self.xmpp.socket.next_sent(timeout)
        self.check_iq(data, sent, use_values)

    def stream_send_presence(self, data, use_values=True, timeout=.1):
        """
        Check that the XMPP client sent the given stanza XML.

        Extracts the next sent stanza and compares it with the given
        XML using check_presence.

        Arguments:
            data       -- The XML string of the expected Presence stanza,
                          or an equivalent stanza object.
            use_values -- Modifies the type of tests used by check_presence.
            timeout    -- Time in seconds to wait for a stanza before
                          failing the check.
        """
        if isinstance(data, str):
            data = self.Presence(xml=ET.fromstring(data))
        sent = self.xmpp.socket.next_sent(timeout)
        self.check_presence(data, sent, use_values)

    def stream_close(self):
        """
        Disconnect the dummy XMPP client.

        Can be safely called even if stream_start has not been called.

        Must be placed in the tearDown method of a test class to ensure
        that the XMPP client is disconnected after an error.
        """
        if hasattr(self, 'xmpp') and self.xmpp is not None:
            self.xmpp.disconnect()
            self.xmpp.socket.recv_data(self.xmpp.stream_footer)

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
            xml    -- The XML object to compare against.
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

        # Step 3: Check text
        if xml.text is None:
            xml.text = ""
        if other.text is None:
            other.text = ""
        xml.text = xml.text.strip()
        other.text = other.text.strip()

        if xml.text != other.text:
            return False

        # Step 4: Recursively check children
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
