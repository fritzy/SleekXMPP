"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""

import unittest
import socket
try:
	import queue
except ImportError:
	import Queue as queue
from xml.etree import cElementTree as ET
from sleekxmpp import ClientXMPP
from sleekxmpp import Message, Iq
from sleekxmpp.stanza.presence import Presence
from sleekxmpp.xmlstream.matcher.stanzapath import StanzaPath
from sleekxmpp.xmlstream.stanzabase import registerStanzaPlugin


class TestSocket(object):
    
    def __init__(self, *args, **kwargs):
        self.socket = socket.socket(*args, **kwargs)
        self.recv_queue = queue.Queue()
        self.send_queue = queue.Queue()

    def __getattr__(self, name):
        """Pass requests through to actual socket"""
        # Override a few methods to prevent actual socket connections
        overrides = {'connect': lambda *args: None,
                     'close': lambda *args: None,
                     'shutdown': lambda *args: None}
        return overrides.get(name, getattr(self.socket, name))

    # ------------------------------------------------------------------
    # Testing Interface

    def nextSent(self, timeout=None):
        """Get the next stanza that has been 'sent'"""
        args = {'block': False}
        if timeout is not None:
            args = {'block': True, 'timeout': timeout}
        try:
            return self.send_queue.get(**args)
        except:
            return None

    def recvData(self, data):
        """Add data to the receiving queue"""
        self.recv_queue.put(data)

    # ------------------------------------------------------------------
    # Socket Interface

    def recv(self, *args, **kwargs):
        return self.read(block=True)

    def send(self, data):
        self.send_queue.put(data)

    # ------------------------------------------------------------------
    # File Socket

    def makefile(self, mode='r', bufsize=-1):
        """File socket version to use with ElementTree"""
        return self

    def read(self, size=4096, block=True, timeout=None):
        """Implement the file socket interface"""
        if timeout is not None:
            block = True
        try:
            return self.recv_queue.get(block, timeout)
        except:
            return None

class TestStream(object):
    """Dummy class to pass a stream object to created stanzas"""
    
    def __init__(self):
        self.default_ns = 'jabber:client'


class SleekTest(unittest.TestCase):
    """
    A SleekXMPP specific TestCase class that provides
    methods for comparing message, iq, and presence stanzas.
    """

    # ------------------------------------------------------------------
    # Shortcut methods for creating stanza objects

    def Message(self, *args, **kwargs):
        """Create a message stanza."""
        return Message(None, *args, **kwargs)

    def Iq(self, *args, **kwargs):
        """Create an iq stanza."""
        return Iq(None, *args, **kwargs)

    def Presence(self, *args, **kwargs):
        """Create a presence stanza."""
        return Presence(None, *args, **kwargs)

    # ------------------------------------------------------------------
    # Methods for comparing stanza objects to XML strings

    def checkMessage(self, msg, xml_string, use_values=True):
        """
        Create and compare several message stanza objects to a 
        correct XML string. 

        If use_values is False, the test using getValues() and 
        setValues() will not be used.
        """

        self.fix_namespaces(msg.xml, 'jabber:client')
        debug = "Given Stanza:\n%s\n" % ET.tostring(msg.xml)

        xml = ET.fromstring(xml_string)
        self.fix_namespaces(xml, 'jabber:client')

        debug += "XML String:\n%s\n" % ET.tostring(xml)
        
        msg2 = self.Message(xml)
        debug += "Constructed Stanza:\n%s\n" % ET.tostring(msg2.xml)
        
        if use_values:
            # Ugly, but need to make sure the type attribute is set.
            msg['type'] = msg['type']
            if xml.attrib.get('type', None) is None:
                xml.attrib['type'] = 'normal'

            values = msg2.getStanzaValues()
            msg3 = self.Message()
            msg3.setStanzaValues(values)
            
            debug += "Second Constructed Stanza:\n%s\n" % ET.tostring(msg3.xml)
            debug = "Three methods for creating stanza do not match:\n" + debug
            self.failUnless(self.compare([xml, msg.xml, msg2.xml, msg3.xml]), 
                            debug)
        else:
            debug = "Two methods for creating stanza do not match:\n" + debug
            self.failUnless(self.compare([xml, msg.xml, msg2.xml]), debug)

    def checkIq(self, iq, xml_string, use_values=True):
        """
        Create and compare several iq stanza objects to a 
        correct XML string. 

        If use_values is False, the test using getValues() and 
        setValues() will not be used.
        """

        self.fix_namespaces(iq.xml, 'jabber:client')
        debug = "Given Stanza:\n%s\n" % ET.tostring(iq.xml)

        xml = ET.fromstring(xml_string)
        self.fix_namespaces(xml, 'jabber:client')
        debug += "XML String:\n%s\n" % ET.tostring(xml)
        
        iq2 = self.Iq(xml)
        debug += "Constructed Stanza:\n%s\n" % ET.tostring(iq2.xml)
        
        if use_values:
            values = iq.getValues()
            iq3 = self.Iq()
            iq3.setValues(values)

            debug += "Second Constructed Stanza:\n%s\n" % ET.tostring(iq3.xml)
            debug = "Three methods for creating stanza do not match:\n" + debug
            self.failUnless(self.compare([xml, iq.xml, iq2.xml, iq3.xml]), 
                            debug)
        else:
            debug = "Two methods for creating stanza do not match:\n" + debug
            self.failUnless(self.compare([xml, iq.xml, iq2.xml]), debug)

    def checkPresence(self, pres, xml_string, use_values=True):
        """
        Create and compare several presence stanza objects to a 
        correct XML string. 

        If use_values is False, the test using getValues() and 
        setValues() will not be used.
        """
        pass

    # ------------------------------------------------------------------
    # Methods for simulating stanza streams.

    def streamStart(self, mode='client', skip=True):
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
            self.xmpp.socket.nextSent(timeout=1)

    def streamRecv(self, data):
        data = str(data)
        self.xmpp.socket.recvData(data)

    def streamSendMessage(self, data, use_values=True, timeout=.5):
        if isinstance(data, str):
            data = self.Message(xml=ET.fromstring(data))
        sent = self.xmpp.socket.nextSent(timeout=1)
        self.checkMessage(data, sent, use_values)
            
    def streamSendIq(self, data, use_values=True, timeout=.5):
        if isinstance(data, str):
            data = self.Iq(xml=ET.fromstring(data))
        sent = self.xmpp.socket.nextSent(timeout)
        self.checkIq(data, sent, use_values)

    def streamSendPresence(self, data, use_values=True, timeout=.5):
        if isinstance(data, str):
            data = self.Presence(xml=ET.fromstring(data))
        sent = self.xmpp.socket.nextSent(timeout)
        self.checkPresence(data, sent, use_values)

    def streamClose(self):
        if self.xmpp is not None:
            self.xmpp.disconnect()
            self.xmpp.socket.recvData(self.xmpp.stream_footer)

    # ------------------------------------------------------------------
    # XML Comparison and Cleanup

    def fix_namespaces(self, xml, ns):
        """
        Assign a namespace to an element and any children that 
        don't have a namespace.
        """
        if xml.tag.startswith('{'):
            return
        xml.tag = '{%s}%s' % (ns, xml.tag)
        for child in xml.getchildren():
            self.fix_namespaces(child, ns)

    def compare(self, xml1, xml2=None):
        """
        Compare XML objects.

        If given a list of XML objects, then
        all of the elements in the list will be
        compared.
        """

        # Compare multiple objects
        if type(xml1) is list:
            xmls = xml1
            xml1 = xmls[0]
            for xml in xmls[1:]:
                xml2 = xml
                if not self.compare(xml1, xml2):
                    return False
            return True

        # Step 1: Check tags
        if xml1.tag != xml2.tag:
            return False

        # Step 2: Check attributes
        if xml1.attrib != xml2.attrib:
            return False

        # Step 3: Recursively check children
        for child in xml1:
            child2s = xml2.findall("%s" % child.tag)
            if child2s is None:
                return False
            for child2 in child2s:
                if self.compare(child, child2):
                    break
            else:
                return False

        # Everything matches
        return True
