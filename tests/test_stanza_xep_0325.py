# -*- coding: utf-8 -*-
"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Sustainable Innovation, Joachim.lindborg@sust.se, bjorn.westrom@consoden.se
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.test import *
import sleekxmpp.plugins.xep_0325 as xep_0325

namespace='sn'

class TestControlStanzas(SleekTest):


    def setUp(self):
        pass

    def testSetRequest(self):
        """
        test of set request stanza
        """
        iq = self.Iq()
        iq['type'] = 'set'
        iq['from'] = 'master@clayster.com/amr'
        iq['to'] = 'device@clayster.com'
        iq['id'] = '1'
        iq['set'].add_node("Device02", "Source02", "MyCacheType")
        iq['set'].add_node("Device15")
        iq['set'].add_data("Tjohej", "boolean", "true")

        self.check(iq,"""
            <iq type='set'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <set xmlns='urn:xmpp:iot:control'>
                    <node nodeId='Device02' sourceId='Source02' cacheType='MyCacheType'/>
                    <node nodeId='Device15'/>
                    <boolean name='Tjohej' value='true'/>
                </set>
            </iq>
        """
            )

        iq['set'].del_node("Device02")

        self.check(iq,"""
            <iq type='set'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <set xmlns='urn:xmpp:iot:control'>
                    <node nodeId='Device15'/>
                    <boolean name='Tjohej' value='true'/>
                </set>
            </iq>
        """
            )

        iq['set'].del_nodes()

        self.check(iq,"""
            <iq type='set'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <set xmlns='urn:xmpp:iot:control'>
                    <boolean name='Tjohej' value='true'/>
                </set>
            </iq>
        """
            )


    def testDirectSet(self):
        """
        test of direct set stanza
        """
        msg = self.Message()
        msg['from'] = 'master@clayster.com/amr'
        msg['to'] = 'device@clayster.com'
        msg['set'].add_node("Device02")
        msg['set'].add_node("Device15")
        msg['set'].add_data("Tjohej", "boolean", "true")

        self.check(msg,"""
            <message
                from='master@clayster.com/amr'
                to='device@clayster.com'>
                <set xmlns='urn:xmpp:iot:control'>
                    <node nodeId='Device02'/>
                    <node nodeId='Device15'/>
                    <boolean name='Tjohej' value='true'/>
                </set>
            </message>
        """
            )


    def testSetResponse(self):
        """
        test of set response stanza
        """
        iq = self.Iq()
        iq['type'] = 'result'
        iq['from'] = 'master@clayster.com/amr'
        iq['to'] = 'device@clayster.com'
        iq['id'] = '8'
        iq['setResponse']['responseCode'] = "OK"

        self.check(iq,"""
            <iq type='result'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='8'>
                <setResponse xmlns='urn:xmpp:iot:control' responseCode='OK' />
            </iq>
        """
            )

        iq = self.Iq()
        iq['type'] = 'error'
        iq['from'] = 'master@clayster.com/amr'
        iq['to'] = 'device@clayster.com'
        iq['id'] = '9'
        iq['setResponse']['responseCode'] = "OtherError"
        iq['setResponse']['error']['var'] = "Output"
        iq['setResponse']['error']['text'] = "Test of other error.!"

        self.check(iq,"""
            <iq type='error'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='9'>
                <setResponse xmlns='urn:xmpp:iot:control' responseCode='OtherError'>
                    <error var='Output'>Test of other error.!</error>
                </setResponse>
            </iq>
        """
            )

        iq = self.Iq()
        iq['type'] = 'error'
        iq['from'] = 'master@clayster.com/amr'
        iq['to'] = 'device@clayster.com'
        iq['id'] = '9'
        iq['setResponse']['responseCode'] = "NotFound"
        iq['setResponse'].add_node("Device17", "Source09")
        iq['setResponse'].add_node("Device18", "Source09")
        iq['setResponse'].add_data("Tjohopp")

        self.check(iq,"""
            <iq type='error'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='9'>
                <setResponse xmlns='urn:xmpp:iot:control' responseCode='NotFound'>
                    <node nodeId='Device17' sourceId='Source09'/>
                    <node nodeId='Device18' sourceId='Source09'/>
                    <parameter name='Tjohopp' />
                </setResponse>
            </iq>
        """
            )

    def testSetRequestDatas(self):
        """
        test of set request data stanzas
        """
        iq = self.Iq()
        iq['type'] = 'set'
        iq['from'] = 'master@clayster.com/amr'
        iq['to'] = 'device@clayster.com'
        iq['id'] = '1'
        iq['set'].add_node("Device02", "Source02", "MyCacheType")
        iq['set'].add_node("Device15")

        iq['set'].add_data("Tjohej", "boolean", "true")
        iq['set'].add_data("Tjohej2", "boolean", "false")

        iq['set'].add_data("TjohejC", "color", "FF00FF")
        iq['set'].add_data("TjohejC2", "color", "00FF00")

        iq['set'].add_data("TjohejS", "string", "String1")
        iq['set'].add_data("TjohejS2", "string", "String2")

        iq['set'].add_data("TjohejDate", "date", "2012-01-01")
        iq['set'].add_data("TjohejDate2", "date", "1900-12-03")

        iq['set'].add_data("TjohejDateT4", "dateTime", "1900-12-03 12:30")
        iq['set'].add_data("TjohejDateT2", "dateTime", "1900-12-03 11:22")

        iq['set'].add_data("TjohejDouble2", "double", "200.22")
        iq['set'].add_data("TjohejDouble3", "double", "-12232131.3333")

        iq['set'].add_data("TjohejDur", "duration", "P5Y")
        iq['set'].add_data("TjohejDur2", "duration", "PT2M1S")

        iq['set'].add_data("TjohejInt", "int", "1")
        iq['set'].add_data("TjohejInt2", "int", "-42")

        iq['set'].add_data("TjohejLong", "long", "123456789098")
        iq['set'].add_data("TjohejLong2", "long", "-90983243827489374")

        iq['set'].add_data("TjohejTime", "time", "23:59")
        iq['set'].add_data("TjohejTime2", "time", "12:00")

        self.check(iq,"""
            <iq type='set'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <set xmlns='urn:xmpp:iot:control'>
                    <node nodeId='Device02' sourceId='Source02' cacheType='MyCacheType'/>
                    <node nodeId='Device15'/>
                    <boolean name='Tjohej' value='true'/>
                    <boolean name='Tjohej2' value='false'/>
                    <color name='TjohejC' value='FF00FF'/>
                    <color name='TjohejC2' value='00FF00'/>
                    <string name='TjohejS' value='String1'/>
                    <string name='TjohejS2' value='String2'/>
                    <date name='TjohejDate' value='2012-01-01'/>
                    <date name='TjohejDate2' value='1900-12-03'/>
                    <dateTime name='TjohejDateT4' value='1900-12-03 12:30'/>
                    <dateTime name='TjohejDateT2' value='1900-12-03 11:22'/>
                    <double name='TjohejDouble2' value='200.22'/>
                    <double name='TjohejDouble3' value='-12232131.3333'/>
                    <duration name='TjohejDur' value='P5Y'/>
                    <duration name='TjohejDur2' value='PT2M1S'/>
                    <int name='TjohejInt' value='1'/>
                    <int name='TjohejInt2' value='-42'/>
                    <long name='TjohejLong' value='123456789098'/>
                    <long name='TjohejLong2' value='-90983243827489374'/>
                    <time name='TjohejTime' value='23:59'/>
                    <time name='TjohejTime2' value='12:00'/>
                </set>
            </iq>
        """
            )

suite = unittest.TestLoader().loadTestsFromTestCase(TestControlStanzas)
