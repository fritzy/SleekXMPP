# -*- coding: utf-8 -*-
"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Sustainable Innovation, Joachim.lindborg@sust.se, bjorn.westrom@consoden.se
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import sys
import datetime
import time
import threading

from sleekxmpp.test import *
from sleekxmpp.xmlstream import ElementBase
from sleekxmpp.plugins.xep_0325.device import Device


class TestStreamControl(SleekTest):

    """
    Test using the XEP-0325 plugin.
    """
    def setUp(self):
        pass

    def _time_now(self):
        return datetime.datetime.now().replace(microsecond=0).isoformat()

    def tearDown(self):
        self.stream_close()

    def testRequestSetOk(self):
        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0325'])

        myDevice = Device("Device22")
        myDevice._add_control_field(name="Temperature", typename="int", value="15")

        self.xmpp['xep_0325'].register_node(nodeId="Device22", device=myDevice, commTimeout=0.5)

        self.recv("""
            <iq type='set'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <set xmlns='urn:xmpp:iot:control'>
                    <int name="Temperature" value="17"/>
                </set>
            </iq>
        """)

        self.send("""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='1'>
                <setResponse xmlns='urn:xmpp:iot:control' responseCode="OK" />
            </iq>
            """)

        self.assertEqual(myDevice._get_field_value("Temperature"), "17")

    def testRequestSetMulti(self):
        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0325'])

        myDevice = Device("Device22")
        myDevice._add_control_field(name="Temperature", typename="int", value="15")
        myDevice._add_control_field(name="Startup", typename="date", value="2013-01-03")

        myDevice2 = Device("Device23")
        myDevice2._add_control_field(name="Temperature", typename="int", value="19")
        myDevice2._add_control_field(name="Startup", typename="date", value="2013-01-09")

        self.xmpp['xep_0325'].register_node(nodeId="Device22", device=myDevice, commTimeout=0.5)
        self.xmpp['xep_0325'].register_node(nodeId="Device23", device=myDevice2, commTimeout=0.5)

        self.recv("""
            <iq type='set'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <set xmlns='urn:xmpp:iot:control'>
                    <node nodeId='Device22' />
                    <int name="Temperature" value="17"/>
                </set>
            </iq>
        """)

        self.send("""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='1'>
                <setResponse xmlns='urn:xmpp:iot:control' responseCode="OK" />
            </iq>
            """)

        self.assertEqual(myDevice._get_field_value("Temperature"), "17")
        self.assertEqual(myDevice2._get_field_value("Temperature"), "19")

        self.recv("""
            <iq type='set'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='2'>
                <set xmlns='urn:xmpp:iot:control'>
                    <node nodeId='Device23' />
                    <node nodeId='Device22' />
                    <date name="Startup" value="2013-02-01"/>
                    <int name="Temperature" value="20"/>
                </set>
            </iq>
        """)

        self.send("""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='2'>
                <setResponse xmlns='urn:xmpp:iot:control' responseCode="OK" />
            </iq>
            """)

        self.assertEqual(myDevice._get_field_value("Temperature"), "20")
        self.assertEqual(myDevice2._get_field_value("Temperature"), "20")
        self.assertEqual(myDevice._get_field_value("Startup"), "2013-02-01")
        self.assertEqual(myDevice2._get_field_value("Startup"), "2013-02-01")

    def testRequestSetFail(self):
        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0325'])

        myDevice = Device("Device23")
        myDevice._add_control_field(name="Temperature", typename="int", value="15")

        self.xmpp['xep_0325'].register_node(nodeId="Device23", device=myDevice, commTimeout=0.5)

        self.recv("""
            <iq type='set'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='9'>
                <set xmlns='urn:xmpp:iot:control'>
                    <int name="Voltage" value="17"/>
                </set>
            </iq>
        """)

        self.send("""
            <iq type='error'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='9'>
                <setResponse xmlns='urn:xmpp:iot:control' responseCode='NotFound'>
                    <parameter name='Voltage' />
                    <error var='Output'>Invalid field Voltage</error>
                </setResponse>
            </iq>
            """)

        self.assertEqual(myDevice._get_field_value("Temperature"), "15")
        self.assertFalse(myDevice.has_control_field("Voltage", "int"))

    def testDirectSetOk(self):
        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0325'])

        myDevice = Device("Device22")
        myDevice._add_control_field(name="Temperature", typename="int", value="15")

        self.xmpp['xep_0325'].register_node(nodeId="Device22", device=myDevice, commTimeout=0.5)

        self.recv("""
            <message
                from='master@clayster.com/amr'
                to='device@clayster.com'>
                <set xmlns='urn:xmpp:iot:control'>
                    <int name="Temperature" value="17"/>
                </set>
            </message>
        """)

        time.sleep(.5)

        self.assertEqual(myDevice._get_field_value("Temperature"), "17")

    def testDirectSetFail(self):
        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0325'])

        myDevice = Device("Device22")
        myDevice._add_control_field(name="Temperature", typename="int", value="15")

        self.xmpp['xep_0325'].register_node(nodeId="Device22", device=myDevice, commTimeout=0.5)

        self.recv("""
            <message
                from='master@clayster.com/amr'
                to='device@clayster.com'>
                <set xmlns='urn:xmpp:iot:control'>
                    <int name="Voltage" value="17"/>
                </set>
            </message>
        """)

        time.sleep(.5)

        self.assertEqual(myDevice._get_field_value("Temperature"), "15")
        self.assertFalse(myDevice.has_control_field("Voltage", "int"))


    def testRequestSetOkAPI(self):

        self.stream_start(mode='client',
                          plugins=['xep_0030',
                                   'xep_0325'])

        results = []

        def my_callback(from_jid, result, nodeIds=None, fields=None, error_msg=None):
            results.append(result)

        fields = []
        fields.append(("Temperature", "double", "20.5"))
        fields.append(("TemperatureAlarmSetting", "string", "High"))

        self.xmpp['xep_0325'].set_request(from_jid="tester@localhost", to_jid="you@google.com", fields=fields, nodeIds=['Device33', 'Device22'], callback=my_callback)

        self.send("""
            <iq type='set'
                from='tester@localhost'
                to='you@google.com'
                id='1'>
                <set xmlns='urn:xmpp:iot:control'>
                    <node nodeId='Device33' />
                    <node nodeId='Device22' />
                    <double name="Temperature" value="20.5" />
                    <string name="TemperatureAlarmSetting" value="High" />
                </set>
            </iq>
            """)

        self.recv("""
            <iq type='result'
                from='you@google.com'
                to='tester@localhost'
                id='1'>
                <setResponse xmlns='urn:xmpp:iot:control' responseCode="OK" />
            </iq>
            """)

        time.sleep(.5)

        self.assertEqual(results, ["OK"])

    def testRequestSetErrorAPI(self):

        self.stream_start(mode='client',
                          plugins=['xep_0030',
                                   'xep_0325'])

        results = []

        def my_callback(from_jid, result, nodeIds=None, fields=None, error_msg=None):
            results.append(result)

        fields = []
        fields.append(("Temperature", "double", "20.5"))
        fields.append(("TemperatureAlarmSetting", "string", "High"))

        self.xmpp['xep_0325'].set_request(from_jid="tester@localhost", to_jid="you@google.com", fields=fields, nodeIds=['Device33', 'Device22'], callback=my_callback)

        self.send("""
            <iq type='set'
                from='tester@localhost'
                to='you@google.com'
                id='1'>
                <set xmlns='urn:xmpp:iot:control'>
                    <node nodeId='Device33' />
                    <node nodeId='Device22' />
                    <double name="Temperature" value="20.5" />
                    <string name="TemperatureAlarmSetting" value="High" />
                </set>
            </iq>
            """)

        self.recv("""
            <iq type='error'
                from='you@google.com'
                to='tester@localhost'
                id='1'>
                <setResponse xmlns='urn:xmpp:iot:control' responseCode="OtherError" >
                    <error var='Temperature'>Sensor error</error>
                </setResponse>
            </iq>
            """)

        time.sleep(.5)

        self.assertEqual(results, ["OtherError"])

    def testServiceDiscoveryClient(self):
        self.stream_start(mode='client',
                          plugins=['xep_0030',
                                   'xep_0325'])

        self.recv("""
        <iq type='get'
                from='master@clayster.com/amr'
                to='tester@localhost'
                id='disco1'>
            <query xmlns='http://jabber.org/protocol/disco#info'/>
        </iq>
        """)

        self.send("""
        <iq type='result'
            to='master@clayster.com/amr'
            id='disco1'>
            <query xmlns='http://jabber.org/protocol/disco#info'>
                <identity category='client' type='bot'/>
                <feature var='urn:xmpp:iot:control'/>
            </query>
        </iq>
        """)

    def testServiceDiscoveryComponent(self):
        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0325'])

        self.recv("""
        <iq type='get'
                from='master@clayster.com/amr'
                to='tester@localhost'
                id='disco1'>
            <query xmlns='http://jabber.org/protocol/disco#info'/>
        </iq>
        """)

        self.send("""
        <iq type='result'
            from='tester@localhost'
            to='master@clayster.com/amr'
            id='disco1'>
            <query xmlns='http://jabber.org/protocol/disco#info'>
                <identity category='component' type='generic'/>
                <feature var='urn:xmpp:iot:control'/>
            </query>
        </iq>
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamControl)

