# -*- encoding:utf-8 -*-

"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Dann Martens (TOMOTON).
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from __future__ import unicode_literals

import base64
import sys

from sleekxmpp.plugins.xep_0009.stanza.RPC import RPCQuery, MethodCall, \
    MethodResponse
from sleekxmpp.plugins.xep_0009.binding import py2xml, xml2py, rpcbase64, \
    rpctime
from sleekxmpp.stanza.iq import Iq
from sleekxmpp.test.sleektest import SleekTest
from sleekxmpp.xmlstream.stanzabase import register_stanza_plugin
from sleekxmpp.xmlstream.tostring import tostring
import unittest


if sys.version_info > (3, 0):
    unicode = str


class TestJabberRPC(SleekTest):

    def setUp(self):
        register_stanza_plugin(Iq, RPCQuery)
        register_stanza_plugin(RPCQuery, MethodCall)
        register_stanza_plugin(RPCQuery, MethodResponse)

    def testMethodCall(self):
        iq = self.Iq()
        iq['rpc_query']['method_call']['method_name'] = 'system.exit'
        iq['rpc_query']['method_call']['params'] = py2xml(*())
        self.check(iq, """
            <iq>
                <query xmlns="jabber:iq:rpc">
                    <methodCall>
                        <methodName>system.exit</methodName>
                        <params />
                    </methodCall>
                </query>
            </iq>
        """, use_values=False)

    def testMethodResponse(self):
        iq = self.Iq()
        iq['rpc_query']['method_response']['params'] = py2xml(*())
        self.check(iq, """
            <iq>
                <query xmlns="jabber:iq:rpc">
                    <methodResponse>
                        <params />
                    </methodResponse>
                </query>
            </iq>
        """, use_values=False)

    def testConvertNil(self):
        params = [None]
        params_xml = py2xml(*params)
        expected_xml = self.parse_xml("""
            <params xmlns="jabber:iq:rpc">
                <param>
                    <value>
                        <nil />
                    </value>
                </param>
            </params>
        """)
        self.assertTrue(self.compare(expected_xml, params_xml),
                        "Nil to XML conversion\nExpected: %s\nGot: %s" % (
                            tostring(expected_xml), tostring(params_xml)))
        self.assertEqual(params, xml2py(expected_xml),
                         "XML to nil conversion")

    def testConvertBoolean(self):
        params = [True, False]
        params_xml = py2xml(*params)
        expected_xml = self.parse_xml("""
            <params xmlns="jabber:iq:rpc">
                <param>
                    <value>
                        <boolean>1</boolean>
                    </value>
                </param>
                <param>
                    <value>
                        <boolean>0</boolean>
                    </value>
                </param>
            </params>
        """)
        self.assertTrue(self.compare(expected_xml, params_xml),
                        "Boolean to XML conversion\nExpected: %s\nGot: %s" % (
                            tostring(expected_xml), tostring(params_xml)))
        self.assertEqual(params, xml2py(expected_xml),
                         "XML to boolean conversion")

    def testConvertString(self):
        params = ["'This' & \"That\""]
        params_xml = py2xml(*params)
        expected_xml = self.parse_xml("""
            <params xmlns="jabber:iq:rpc">
                <param>
                    <value>
                        <string>&apos;This&apos; &amp; &quot;That&quot;</string>
                    </value>
                </param>
            </params>
        """)
        self.assertTrue(self.compare(expected_xml, params_xml),
                        "String to XML conversion\nExpected: %s\nGot: %s" % (
                            tostring(expected_xml), tostring(params_xml)))
        self.assertEqual(params, xml2py(expected_xml),
                        "XML to string conversion")

    def testConvertUnicodeString(self):
        params = ["おはよう"]
        params_xml = py2xml(*params)
        expected_xml = self.parse_xml("""
            <params xmlns="jabber:iq:rpc">
                <param>
                    <value>
                        <string>おはよう</string>
                    </value>
                </param>
            </params>
        """)
        self.assertTrue(self.compare(expected_xml, params_xml),
                        "String to XML conversion\nExpected: %s\nGot: %s" % (
                            tostring(expected_xml), tostring(params_xml)))
        self.assertEqual(params, xml2py(expected_xml),
                        "XML to string conversion")

    def testConvertInteger(self):
        params = [32767, -32768]
        params_xml = py2xml(*params)
        expected_xml = self.parse_xml("""
            <params xmlns="jabber:iq:rpc">
                <param>
                    <value>
                        <i4>32767</i4>
                    </value>
                </param>
                <param>
                    <value>
                        <i4>-32768</i4>
                    </value>
                </param>
            </params>
        """)
        alternate_xml = self.parse_xml("""
            <params xmlns="jabber:iq:rpc">
                <param>
                    <value>
                        <int>32767</int>
                    </value>
                </param>
                <param>
                    <value>
                        <int>-32768</int>
                    </value>
                </param>
            </params>
        """)
        self.assertTrue(self.compare(expected_xml, params_xml),
                        "Integer to XML conversion\nExpected: %s\nGot: %s" % (
                            tostring(expected_xml), tostring(params_xml)))
        self.assertEqual(params, xml2py(expected_xml),
                         "XML to boolean conversion")
        self.assertEqual(params, xml2py(alternate_xml),
                         "Alternate XML to boolean conversion")


    def testConvertDouble(self):
        params = [3.14159265]
        params_xml = py2xml(*params)
        expected_xml = self.parse_xml("""
            <params xmlns="jabber:iq:rpc">
                <param>
                    <value>
                        <double>3.14159265</double>
                    </value>
                </param>
            </params>
        """)
        self.assertTrue(self.compare(expected_xml, params_xml),
                        "Double to XML conversion\nExpected: %s\nGot: %s" % (
                            tostring(expected_xml), tostring(params_xml)))
        self.assertEqual(params, xml2py(expected_xml),
                         "XML to double conversion")

    def testConvertBase64(self):
        params = [rpcbase64(base64.b64encode(b"Hello, world!"))]
        params_xml = py2xml(*params)
        expected_xml = self.parse_xml("""
            <params xmlns="jabber:iq:rpc">
                <param>
                    <value>
                        <base64>SGVsbG8sIHdvcmxkIQ==</base64>
                    </value>
                </param>
            </params>
        """)
        alternate_xml = self.parse_xml("""
            <params xmlns="jabber:iq:rpc">
                <param>
                    <value>
                        <Base64>SGVsbG8sIHdvcmxkIQ==</Base64>
                    </value>
                </param>
            </params>
        """)
        self.assertTrue(self.compare(expected_xml, params_xml),
                        "Base64 to XML conversion\nExpected: %s\nGot: %s" % (
                            tostring(expected_xml), tostring(params_xml)))
        self.assertEqual(list(map(lambda x: x.decode(), params)),
                         list(map(lambda x: x.decode(), xml2py(expected_xml))),
                         "XML to base64 conversion")
        self.assertEqual(list(map(lambda x: x.decode(), params)),
                         list(map(lambda x: x.decode(), xml2py(alternate_xml))),
                         "Alternate XML to base64 conversion")

    def testConvertDateTime(self):
        params = [rpctime("20111220T01:50:00")]
        params_xml = py2xml(*params)
        expected_xml = self.parse_xml("""
            <params xmlns="jabber:iq:rpc">
                <param>
                    <value>
                        <dateTime.iso8601>20111220T01:50:00</dateTime.iso8601>
                    </value>
                </param>
            </params>
        """)
        self.assertTrue(self.compare(expected_xml, params_xml),
                        "DateTime to XML conversion\nExpected: %s\nGot: %s" % (
                            tostring(expected_xml), tostring(params_xml)))
        self.assertEqual(list(map(lambda x: x.iso8601(), params)),
                         list(map(lambda x: x.iso8601(), xml2py(expected_xml))),
                         None)

    def testConvertArray(self):
        params = [[1,2,3], ('a', 'b', 'c')]
        params_xml = py2xml(*params)
        expected_xml = self.parse_xml("""
            <params xmlns="jabber:iq:rpc">
                <param>
                    <value>
                        <array>
                            <data>
                                <value><i4>1</i4></value>
                                <value><i4>2</i4></value>
                                <value><i4>3</i4></value>
                            </data>
                        </array>
                    </value>
                </param>
                <param>
                    <value>
                        <array>
                            <data>
                                <value><string>a</string></value>
                                <value><string>b</string></value>
                                <value><string>c</string></value>
                            </data>
                        </array>
                    </value>
                </param>
            </params>
        """)
        self.assertTrue(self.compare(expected_xml, params_xml),
                        "Array to XML conversion\nExpected: %s\nGot: %s" % (
                            tostring(expected_xml), tostring(params_xml)))
        self.assertEqual(list(map(list, params)), xml2py(expected_xml),
                         "XML to array conversion")

    def testConvertStruct(self):
        params = [{"foo": "bar", "baz": False}]
        params_xml = py2xml(*params)
        expected_xml = self.parse_xml("""
            <params xmlns="jabber:iq:rpc">
                <param>
                    <value>
                        <struct>
                            <member>
                                <name>foo</name>
                                <value><string>bar</string></value>
                            </member>
                            <member>
                                <name>baz</name>
                                <value><boolean>0</boolean></value>
                            </member>
                        </struct>
                    </value>
                </param>
            </params>
        """)
        self.assertTrue(self.compare(expected_xml, params_xml),
                        "Struct to XML conversion\nExpected: %s\nGot: %s" % (
                            tostring(expected_xml), tostring(params_xml)))
        self.assertEqual(params, xml2py(expected_xml),
                         "XML to struct conversion")

suite = unittest.TestLoader().loadTestsFromTestCase(TestJabberRPC)

