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
from sleekxmpp.test import TestSocket, TestLiveSocket
from sleekxmpp.xmlstream import StanzaBase, ET, register_stanza_plugin
from sleekxmpp.xmlstream.tostring import tostring


class SleekTest(unittest.TestCase):

    """
    A SleekXMPP specific TestCase class that provides
    methods for comparing message, iq, and presence stanzas.

    Methods:
        Message              -- Create a Message stanza object.
        Iq                   -- Create an Iq stanza object.
        Presence             -- Create a Presence stanza object.
        check_jid            -- Check a JID and its component parts.
        check                -- Compare a stanza against an XML string.
        stream_start         -- Initialize a dummy XMPP client.
        stream_close         -- Disconnect the XMPP client.
        make_header          -- Create a stream header.
        send_header          -- Check that the given header has been sent.
        send_feature         -- Send a raw XML element.
        send                 -- Check that the XMPP client sent the given
                                generic stanza.
        recv                 -- Queue data for XMPP client to receive, or
                                verify the data that was received from a
                                live connection.
        recv_header          -- Check that a given stream header
                                was received.
        recv_feature         -- Check that a given, raw XML element
                                was recveived.
        fix_namespaces       -- Add top-level namespace to an XML object.
        compare              -- Compare XML objects against each other.
    """

    def runTest(self):
        pass

    def parse_xml(self, xml_string):
        try:
            xml = ET.fromstring(xml_string)
            return xml
        except SyntaxError as e:
            if 'unbound' in e.msg:
                known_prefixes = {
                        'stream': 'http://etherx.jabber.org/streams'}

                prefix = xml_string.split('<')[1].split(':')[0]
                if prefix in known_prefixes:
                    xml_string = '<fixns xmlns:%s="%s">%s</fixns>' % (
                            prefix,
                            known_prefixes[prefix],
                            xml_string)
                xml = self.parse_xml(xml_string)
                xml = xml.getchildren()[0]
                return xml

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

    def check_jid(self, jid, user=None, domain=None, resource=None,
                  bare=None, full=None, string=None):
        """
        Verify the components of a JID.

        Arguments:
            jid      -- The JID object to test.
            user     -- Optional. The user name portion of the JID.
            domain   -- Optional. The domain name portion of the JID.
            resource -- Optional. The resource portion of the JID.
            bare     -- Optional. The bare JID.
            full     -- Optional. The full JID.
            string   -- Optional. The string version of the JID.
        """
        if user is not None:
            self.assertEqual(jid.user, user,
                    "User does not match: %s" % jid.user)
        if domain is not None:
            self.assertEqual(jid.domain, domain,
                    "Domain does not match: %s" % jid.domain)
        if resource is not None:
            self.assertEqual(jid.resource, resource,
                    "Resource does not match: %s" % jid.resource)
        if bare is not None:
            self.assertEqual(jid.bare, bare,
                    "Bare JID does not match: %s" % jid.bare)
        if full is not None:
            self.assertEqual(jid.full, full,
                    "Full JID does not match: %s" % jid.full)
        if string is not None:
            self.assertEqual(str(jid), string,
                    "String does not match: %s" % str(jid))

    # ------------------------------------------------------------------
    # Methods for comparing stanza objects to XML strings

    def check(self, stanza, xml_string,
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
        stanza_class = stanza.__class__
        xml = self.parse_xml(xml_string)

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
                known_defaults = {
                    Message: ['type'],
                    Presence: ['priority']
                }
                defaults = known_defaults.get(stanza_class, [])
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

    # ------------------------------------------------------------------
    # Methods for simulating stanza streams.

    def stream_start(self, mode='client', skip=True, header=None,
                           socket='mock', jid='tester@localhost',
                           password='test', server='localhost',
                           port=5222):
        """
        Initialize an XMPP client or component using a dummy XML stream.

        Arguments:
            mode     -- Either 'client' or 'component'. Defaults to 'client'.
            skip     -- Indicates if the first item in the sent queue (the
                        stream header) should be removed. Tests that wish
                        to test initializing the stream should set this to
                        False. Otherwise, the default of True should be used.
            socket   -- Either 'mock' or 'live' to indicate if the socket
                        should be a dummy, mock socket or a live, functioning
                        socket. Defaults to 'mock'.
            jid      -- The JID to use for the connection.
                        Defaults to 'tester@localhost'.
            password -- The password to use for the connection.
                        Defaults to 'test'.
            server   -- The name of the XMPP server. Defaults to 'localhost'.
            port     -- The port to use when connecting to the server.
                        Defaults to 5222.
        """
        if mode == 'client':
            self.xmpp = ClientXMPP(jid, password)
        elif mode == 'component':
            self.xmpp = ComponentXMPP(jid, password,
                                      server, port)
        else:
            raise ValueError("Unknown XMPP connection mode.")

        if socket == 'mock':
            self.xmpp.set_socket(TestSocket())

            # Simulate connecting for mock sockets.
            self.xmpp.auto_reconnect = False
            self.xmpp.is_client = True
            self.xmpp.state._set_state('connected')

            # Must have the stream header ready for xmpp.process() to work.
            if not header:
                header = self.xmpp.stream_header
            self.xmpp.socket.recv_data(header)
        elif socket == 'live':
            self.xmpp.socket_class = TestLiveSocket
            self.xmpp.connect()
        else:
            raise ValueError("Unknown socket type.")

        self.xmpp.register_plugins()
        self.xmpp.process(threaded=True)
        if skip:
            # Clear startup stanzas
            self.xmpp.socket.next_sent(timeout=1)
            if mode == 'component':
                self.xmpp.socket.next_sent(timeout=1)

    def make_header(self, sto='',
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

    def recv(self, data, stanza_class=StanzaBase, defaults=[],
             use_values=True, timeout=1):
        """
        Pass data to the dummy XMPP client as if it came from an XMPP server.

        If using a live connection, verify what the server has sent.

        Arguments:
            data         -- String stanza XML to be received and processed by
                            the XMPP client or component.
            stanza_class -- The stanza object class for verifying data received
                            by a live connection. Defaults to StanzaBase.
            defaults     -- A list of stanza interfaces with default values that
                            may interfere with comparisons.
            use_values   -- Indicates if stanza comparisons should test using
                            getStanzaValues() and setStanzaValues().
                            Defaults to True.
            timeout      -- Time to wait in seconds for data to be received by
                            a live connection.
        """
        if self.xmpp.socket.is_live:
            # we are working with a live connection, so we should
            # verify what has been received instead of simulating
            # receiving data.
            recv_data = self.xmpp.socket.next_recv(timeout)
            if recv_data is None:
                return False
            stanza = stanza_class(xml=self.parse_xml(recv_data))
            return self.check(stanza_class, stanza, data,
                                     defaults=defaults,
                                     use_values=use_values)
        else:
            # place the data in the dummy socket receiving queue.
            data = str(data)
            self.xmpp.socket.recv_data(data)

    def recv_header(self, sto='',
                          sfrom='',
                          sid='',
                          stream_ns="http://etherx.jabber.org/streams",
                          default_ns="jabber:client",
                          version="1.0",
                          xml_header=False,
                          timeout=1):
        """
        Check that a given stream header was received.

        Arguments:
            sto        -- The recipient of the stream header.
            sfrom      -- The agent sending the stream header.
            sid        -- The stream's id. Set to None to ignore.
            stream_ns  -- The namespace of the stream's root element.
            default_ns -- The default stanza namespace.
            version    -- The stream version.
            xml_header -- Indicates if the XML version header should be
                          appended before the stream header.
            timeout    -- Length of time to wait in seconds for a
                          response.
        """
        header = self.make_header(sto, sfrom, sid,
                                  stream_ns=stream_ns,
                                  default_ns=default_ns,
                                  version=version,
                                  xml_header=xml_header)
        recv_header = self.xmpp.socket.next_recv(timeout)
        if recv_header is None:
            raise ValueError("Socket did not return data.")

        # Apply closing elements so that we can construct
        # XML objects for comparison.
        header2 = header + '</stream:stream>'
        recv_header2 = recv_header + '</stream:stream>'

        xml = self.parse_xml(header2)
        recv_xml = self.parse_xml(recv_header2)

        if sid is None:
            # Ignore the id sent by the server since
            # we can't know in advance what it will be.
            if 'id' in recv_xml.attrib:
                del recv_xml.attrib['id']

        # Ignore the xml:lang attribute for now.
        if 'xml:lang' in recv_xml.attrib:
            del recv_xml.attrib['xml:lang']
        xml_ns = 'http://www.w3.org/XML/1998/namespace'
        if '{%s}lang' % xml_ns in recv_xml.attrib:
            del recv_xml.attrib['{%s}lang' % xml_ns]

        if recv_xml.getchildren:
            # We received more than just the header
            for xml in recv_xml.getchildren():
                self.xmpp.socket.recv_data(tostring(xml))

            attrib = recv_xml.attrib
            recv_xml.clear()
            recv_xml.attrib = attrib

        self.failUnless(
            self.compare(xml, recv_xml),
            "Stream headers do not match:\nDesired:\n%s\nReceived:\n%s" % (
                '%s %s' % (xml.tag, xml.attrib),
                '%s %s' % (recv_xml.tag, recv_xml.attrib)))

    def recv_feature(self, data, use_values=True, timeout=1):
        """
        """
        if self.xmpp.socket.is_live:
            # we are working with a live connection, so we should
            # verify what has been received instead of simulating
            # receiving data.
            recv_data = self.xmpp.socket.next_recv(timeout)
            if recv_data is None:
                return False
            xml = self.parse_xml(data)
            recv_xml = self.parse_xml(recv_data)
            self.failUnless(self.compare(xml, recv_xml),
                "Features do not match.\nDesired:\n%s\nReceived:\n%s" % (
                    tostring(xml), tostring(recv_xml)))
        else:
            # place the data in the dummy socket receiving queue.
            data = str(data)
            self.xmpp.socket.recv_data(data)

    def send_header(self, sto='',
                          sfrom='',
                          sid='',
                          stream_ns="http://etherx.jabber.org/streams",
                          default_ns="jabber:client",
                          version="1.0",
                          xml_header=False,
                          timeout=1):
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
        header = self.make_header(sto, sfrom, sid,
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
        sent_header2 = sent_header + b'</stream:stream>'

        xml = self.parse_xml(header2)
        sent_xml = self.parse_xml(sent_header2)

        self.failUnless(
            self.compare(xml, sent_xml),
            "Stream headers do not match:\nDesired:\n%s\nSent:\n%s" % (
                header, sent_header))

    def send_feature(self, data, use_values=True, timeout=1):
        """
        """
        sent_data = self.xmpp.socket.next_sent(timeout)
        if sent_data is None:
            return False
        xml = self.parse_xml(data)
        sent_xml = self.parse_xml(sent_data)
        self.failUnless(self.compare(xml, sent_xml),
            "Features do not match.\nDesired:\n%s\nSent:\n%s" % (
                tostring(xml), tostring(sent_xml)))

    def send(self, data, defaults=None,
             use_values=True, timeout=.1):
        """
        Check that the XMPP client sent the given stanza XML.

        Extracts the next sent stanza and compares it with the given
        XML using check.

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
        if isinstance(data, str):
            xml = self.parse_xml(data)
            self.fix_namespaces(xml, 'jabber:client')
            data = self.xmpp._build_stanza(xml, 'jabber:client')
        sent = self.xmpp.socket.next_sent(timeout)
        self.check(data, sent,
                          defaults=defaults,
                          use_values=use_values)

    def stream_close(self):
        """
        Disconnect the dummy XMPP client.

        Can be safely called even if stream_start has not been called.

        Must be placed in the tearDown method of a test class to ensure
        that the XMPP client is disconnected after an error.
        """
        if hasattr(self, 'xmpp') and self.xmpp is not None:
            self.xmpp.socket.recv_data(self.xmpp.stream_footer)
            self.xmpp.disconnect()

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

        # Step 4: Check children count
        if len(xml.getchildren()) != len(other.getchildren()):
            return False

        # Step 5: Recursively check children
        for child in xml:
            child2s = other.findall("%s" % child.tag)
            if child2s is None:
                return False
            for child2 in child2s:
                if self.compare(child, child2):
                    break
            else:
                return False

        # Step 6: Recursively check children the other way.
        for child in other:
            child2s = xml.findall("%s" % child.tag)
            if child2s is None:
                return False
            for child2 in child2s:
                if self.compare(child, child2):
                    break
            else:
                return False

        # Everything matches
        return True
