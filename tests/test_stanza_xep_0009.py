"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Dann Martens (TOMOTON).
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.plugins.xep_0009.stanza.RPC import RPCQuery, MethodCall, \
    MethodResponse
from sleekxmpp.plugins.xep_0009.binding import py2xml
from sleekxmpp.stanza.iq import Iq
from sleekxmpp.test.sleektest import SleekTest
from sleekxmpp.xmlstream.stanzabase import register_stanza_plugin
import unittest



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
        
suite = unittest.TestLoader().loadTestsFromTestCase(TestJabberRPC)        
        
