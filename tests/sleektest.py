"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""

import unittest
from xml.etree import cElementTree as ET
from sleekxmpp import Message, Iq
from sleekxmpp.stanza.presence import Presence
from sleekxmpp.xmlstream.matcher.stanzapath import StanzaPath


class SleekTest(unittest.TestCase):
    """
    A SleekXMPP specific TestCase class that provides
    methods for comparing message, iq, and presence stanzas.
    """

    def stanzaPlugin(self, stanza, plugin):
        """
        Associate a stanza object as a plugin for another stanza.
        """
        tag = "{%s}%s" % (plugin.namespace, plugin.name)
	stanza.plugin_attrib_map[plugin.plugin_attrib] = plugin
	stanza.plugin_tag_map[tag] = plugin

    def Message(self, *args, **kwargs):
        """Create a message stanza."""
        return Message(None, *args, **kwargs)

    def Iq(self, *args, **kwargs):
        """Create an iq stanza."""
        return Iq(None, *args, **kwargs)

    def Presence(self, *args, **kwargs):
        """Create a presence stanza."""
        return Presence(None, *args, **kwargs)

    def checkMessage(self, msg, xml_string, use_values=True):
        """
        Create and compare several message stanza objects to a 
        correct XML string. 

        If use_values is False, the test using getValues() and 
        setValues() will not be used.
        """

        debug = "Given Stanza:\n%s\n" % ET.tostring(msg.xml)

        xml = ET.fromstring(xml_string)
        xml.tag = '{jabber:client}message'
        debug += "XML String:\n%s\n" % ET.tostring(xml)
        
        msg2 = self.Message(xml)
        debug += "Constructed Stanza:\n%s\n" % ET.tostring(msg2.xml)
        
        if use_values:
            # Ugly, but need to make sure the type attribute is set.
            msg['type'] = msg['type']
            if xml.attrib.get('type', None) is None:
                xml.attrib['type'] = 'normal'

            values = msg2.getValues()
            msg3 = self.Message()
            msg3.setValues(values)
            
            debug += "Second Constructed Stanza:\n%s\n" % ET.tostring(msg3.xml)
            debug = "Three methods for creating stanza do not match:\n" + debug
            self.failUnless(self.compare([xml, msg.xml, 
                                          msg2.xml, msg3.xml]), 
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
        debug = "Given Stanza:\n%s\n" % ET.tostring(iq.xml)

        xml = ET.fromstring(xml_string)
        xml.tag = '{jabber:client}iq'
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
            print xml1.tag, xml2.tag
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
