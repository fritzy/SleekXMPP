# -*- coding: utf-8 -*-

import sys
import datetime
import time
import threading

from sleekxmpp.test import *
from sleekxmpp.xmlstream import ElementBase
from sleekxmpp.plugins.xep_0323.device import Device


class TestStreamSensorData(SleekTest):

    """
    Test using the XEP-0323 plugin.
    """
    def setUp(self):
        pass

    def _time_now(self):
        return datetime.datetime.now().replace(microsecond=0).isoformat()

    def tearDown(self):
        self.stream_close()

    def testRequestAccept(self):
        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0323'])

        myDevice = Device("Device22")
        myDevice._add_field(name="Temperature", typename="numeric", unit="°C")
        myDevice._set_momentary_timestamp("2013-03-07T16:24:30")
        myDevice._add_field_momentary_data("Temperature", "23.4", flags={"automaticReadout": "true"})

        self.xmpp['xep_0323'].register_node(nodeId="Device22", device=myDevice, commTimeout=0.5)

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1' momentary='true'/>
            </iq>
        """)

        self.send("""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='1'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='1'/>
            </iq>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='1' done='true'>
                    <node nodeId='Device22'>
                        <timestamp value='2013-03-07T16:24:30'>
                            <numeric name='Temperature' momentary='true' automaticReadout='true' value='23.4' unit='°C'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
            """)

    def testRequestRejectAuth(self):

        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0323'])

        self.xmpp['xep_0323']._set_authenticated("darth@deathstar.com")

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='4'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='5' momentary='true'/>
            </iq>
        """)

        self.send("""
            <iq type='error'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='4'>
                <rejected xmlns='urn:xmpp:iot:sensordata' seqnr='5'>
                    <error>Access denied</error>
                </rejected>
            </iq>
            """)

    def testRequestNode(self):

        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0323'])

        myDevice = Device("Device44")
        self.xmpp['xep_0323'].register_node('Device44', myDevice, commTimeout=0.5)

        print("."),

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='77'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='66' momentary='true'>
                    <node nodeId='Device33'/>
                </req>
            </iq>
        """)

        self.send("""
            <iq type='error'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='77'>
                <rejected xmlns='urn:xmpp:iot:sensordata' seqnr='66'>
                    <error>Invalid nodeId Device33</error>
                </rejected>
            </iq>
            """)

        print("."),

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='8'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='7' momentary='true'>
                    <node nodeId='Device44'/>
                </req>
            </iq>
        """)

        self.send("""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='8'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='7'/>
            </iq>
            """)


    def testRequestField(self):

        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0323'])

        myDevice = Device("Device44")
        myDevice._add_field(name='Voltage', typename="numeric", unit="V")
        myDevice._add_field_timestamp_data(name="Voltage", value="230.4", timestamp="2000-01-01T00:01:02", flags={"invoiced": "true"})

        self.xmpp['xep_0323'].register_node('Device44', myDevice, commTimeout=0.5)

        print("."),

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='7'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='6'>
                    <field name='Current'/>
                </req>
            </iq>
        """)

        self.send("""
            <iq type='error'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='7'>
                <rejected xmlns='urn:xmpp:iot:sensordata' seqnr='6'>
                    <error>Invalid field Current</error>
                </rejected>
            </iq>
            """)

        print("."),

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='8'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='7'>
                    <field name='Voltage'/>
                </req>
            </iq>
        """)

        self.send("""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='8'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='7'/>
            </iq>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='7'>
                    <node nodeId='Device44'>
                        <timestamp value='2000-01-01T00:01:02'>
                            <numeric name='Voltage' invoiced='true' value='230.4' unit='V'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='7' done='true'>
                </fields>
            </message>
            """)

    def testRequestMultiTimestampSingleField(self):

        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0323'])

        myDevice = Device("Device44")
        myDevice._add_field(name='Voltage', typename="numeric", unit="V")
        myDevice._add_field_timestamp_data(name="Voltage", value="230.4", timestamp="2000-01-01T00:01:02", flags={"invoiced": "true"})
        myDevice._add_field(name='Current', typename="numeric", unit="A")
        myDevice._add_field(name='Height', typename="string")
        myDevice._add_field_timestamp_data(name="Voltage", value="230.6", timestamp="2000-01-01T01:01:02")
        myDevice._add_field_timestamp_data(name="Height", value="115 m", timestamp="2000-01-01T01:01:02", flags={"invoiced": "true"})

        self.xmpp['xep_0323'].register_node('Device44', myDevice, commTimeout=0.5)

        print("."),

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='8'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='7'>
                    <field name='Voltage'/>
                </req>
            </iq>
        """)

        self.send("""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='8'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='7'/>
            </iq>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='7'>
                    <node nodeId='Device44'>
                        <timestamp value='2000-01-01T00:01:02'>
                            <numeric name='Voltage' invoiced='true' value='230.4' unit='V'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='7'>
                    <node nodeId='Device44'>
                        <timestamp value='2000-01-01T01:01:02'>
                            <numeric name='Voltage' value='230.6' unit='V'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='7' done='true'>
                </fields>
            </message>
            """)

    def testRequestMultiTimestampAllFields(self):

        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0323'])

        myDevice = Device("Device44")
        myDevice._add_field(name='Voltage', typename="numeric", unit="V")
        myDevice._add_field_timestamp_data(name="Voltage", value="230.4", timestamp="2000-01-01T00:01:02", flags={"invoiced": "true"})
        myDevice._add_field(name='Current', typename="numeric", unit="A")
        myDevice._add_field(name='Height', typename="string")
        myDevice._add_field_timestamp_data(name="Voltage", value="230.6", timestamp="2000-01-01T01:01:02")
        myDevice._add_field_timestamp_data(name="Height", value="115 m", timestamp="2000-01-01T01:01:02", flags={"invoiced": "true"})

        self.xmpp['xep_0323'].register_node('Device44', myDevice, commTimeout=0.5)

        print("."),

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='8'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='7'/>
            </iq>
        """)

        self.send("""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='8'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='7'/>
            </iq>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='7'>
                    <node nodeId='Device44'>
                        <timestamp value='2000-01-01T00:01:02'>
                            <numeric name='Voltage' invoiced='true' value='230.4' unit='V'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='7'>
                    <node nodeId='Device44'>
                        <timestamp value='2000-01-01T01:01:02'>
                            <numeric name='Voltage' value='230.6' unit='V'/>
                            <string name='Height' invoiced='true' value='115 m'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='7' done='true'>
                </fields>
            </message>
            """)

    def testRequestAPI(self):

        self.stream_start(mode='client',
                          plugins=['xep_0030',
                                   'xep_0323'])

        self.xmpp['xep_0323'].request_data(from_jid="tester@localhost", to_jid="you@google.com", callback=None)

        self.send("""
            <iq type='get'
                from='tester@localhost'
                to='you@google.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1'/>
            </iq>
            """)

        self.xmpp['xep_0323'].request_data(from_jid="tester@localhost", to_jid="you@google.com", nodeIds=['Device33', 'Device22'], callback=None)

        self.send("""
            <iq type='get'
                from='tester@localhost'
                to='you@google.com'
                id='2'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='2'>
                    <node nodeId="Device33"/>
                    <node nodeId="Device22"/>
                </req>
            </iq>
            """)

        self.xmpp['xep_0323'].request_data(from_jid="tester@localhost", to_jid="you@google.com", fields=['Temperature', 'Voltage'], callback=None)

        self.send("""
            <iq type='get'
                from='tester@localhost'
                to='you@google.com'
                id='3'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='3'>
                    <field name="Temperature"/>
                    <field name="Voltage"/>
                </req>
            </iq>
            """)

    def testRequestRejectAPI(self):

        self.stream_start(mode='client',
                          plugins=['xep_0030',
                                   'xep_0323'])

        results = []

        def my_callback(from_jid, result, nodeId=None, timestamp=None, fields=None, error_msg=None):
            if (result == "rejected") and (error_msg == "Invalid device Device22"):
                results.append("rejected")

        self.xmpp['xep_0323'].request_data(from_jid="tester@localhost", to_jid="you@google.com", nodeIds=['Device33', 'Device22'], callback=my_callback)

        self.send("""
            <iq type='get'
                from='tester@localhost'
                to='you@google.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <node nodeId="Device33"/>
                    <node nodeId="Device22"/>
                </req>
            </iq>
            """)

        self.recv("""
            <iq type='error'
                from='you@google.com'
                to='tester@localhost'
                id='1'>
                <rejected xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <error>Invalid device Device22</error>
                </rejected>
            </iq>
            """)

        time.sleep(.1)

        self.failUnless(results == ["rejected"],
                "Rejected callback was not properly executed")

    def testRequestAcceptedAPI(self):

        self.stream_start(mode='client',
                          plugins=['xep_0030',
                                   'xep_0323'])

        results = []

        def my_callback(from_jid, result, nodeId=None, timestamp=None, fields=None, error_msg=None):
            results.append(result)

        self.xmpp['xep_0323'].request_data(from_jid="tester@localhost", to_jid="you@google.com", nodeIds=['Device33', 'Device22'], callback=my_callback)

        self.send("""
            <iq type='get'
                from='tester@localhost'
                to='you@google.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <node nodeId="Device33"/>
                    <node nodeId="Device22"/>
                </req>
            </iq>
            """)

        self.recv("""
            <iq type='result'
                from='you@google.com'
                to='tester@localhost'
                id='1'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='1'/>
            </iq>
            """)

        time.sleep(.1)

        self.failUnless(results == ["accepted"],
                "Accepted callback was not properly executed")

    def testRequestFieldsAPI(self):

        self.stream_start(mode='client',
                          plugins=['xep_0030',
                                   'xep_0323'])

        results = []
        callback_data = {}

        def my_callback(from_jid, result, nodeId=None, timestamp=None, fields=None, error_msg=None):
            results.append(result)
            if result == "fields":
                callback_data["nodeId"] = nodeId
                callback_data["timestamp"] = timestamp
                callback_data["error_msg"] = error_msg
                for f in fields:
                    callback_data["field_" + f['name']] = f

        t1= threading.Thread(name="request_data",
                         target=self.xmpp['xep_0323'].request_data,
                         kwargs={"from_jid": "tester@localhost",
                                    "to_jid": "you@google.com",
                                    "nodeIds": ['Device33'],
                                    "callback": my_callback})
        t1.start()
        #self.xmpp['xep_0323'].request_data(from_jid="tester@localhost", to_jid="you@google.com", nodeIds=['Device33'], callback=my_callback);

        self.send("""
            <iq type='get'
                from='tester@localhost'
                to='you@google.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <node nodeId="Device33"/>
                </req>
            </iq>
            """)

        self.recv("""
            <iq type='result'
                from='you@google.com'
                to='tester@localhost'
                id='1'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='1'/>
            </iq>
            """)

        self.recv("""
            <message from='you@google.com'
                     to='tester@localhost'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <node nodeId='Device33'>
                        <timestamp value='2000-01-01T00:01:02'>
                            <numeric name='Voltage' invoiced='true' value='230.4' unit='V'/>
                            <boolean name='TestBool' value='true'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
            """)

        self.recv("""
            <message from='you@google.com'
                     to='tester@localhost'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='1' done='true'/>
            </message>
            """)

        t1.join()
        time.sleep(.5)

        self.failUnlessEqual(results, ["accepted","fields","done"])
        # self.assertIn("nodeId", callback_data);
        self.assertTrue("nodeId" in callback_data)
        self.failUnlessEqual(callback_data["nodeId"], "Device33")
        # self.assertIn("timestamp", callback_data);
        self.assertTrue("timestamp" in callback_data)
        self.failUnlessEqual(callback_data["timestamp"], "2000-01-01T00:01:02")
        #self.assertIn("field_Voltage", callback_data);
        self.assertTrue("field_Voltage" in callback_data)
        self.failUnlessEqual(callback_data["field_Voltage"], {"name": "Voltage", "value": "230.4", "typename": "numeric", "unit": "V", "flags": {"invoiced": "true"}})
        #self.assertIn("field_TestBool", callback_data);
        self.assertTrue("field_TestBool" in callback_data)
        self.failUnlessEqual(callback_data["field_TestBool"], {"name": "TestBool", "value": "true", "typename": "boolean" })

    def testServiceDiscoveryClient(self):
        self.stream_start(mode='client',
                          plugins=['xep_0030',
                                   'xep_0323'])

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
                <feature var='urn:xmpp:iot:sensordata'/>
            </query>
        </iq>
        """)

    def testServiceDiscoveryComponent(self):
        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0323'])

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
                <feature var='urn:xmpp:iot:sensordata'/>
            </query>
        </iq>
        """)

    def testRequestTimeout(self):

        self.stream_start(mode='client',
                          plugins=['xep_0030',
                                   'xep_0323'])

        results = []
        callback_data = {}

        def my_callback(from_jid, result, nodeId=None, timestamp=None, error_msg=None):
            results.append(result)
            if result == "failure":
                callback_data["nodeId"] = nodeId
                callback_data["timestamp"] = timestamp
                callback_data["error_msg"] = error_msg

        t1= threading.Thread(name="request_data",
                         target=self.xmpp['xep_0323'].request_data,
                         kwargs={"from_jid": "tester@localhost",
                                    "to_jid": "you@google.com",
                                    "nodeIds": ['Device33'],
                                    "callback": my_callback})
        t1.start()

        self.send("""
            <iq type='get'
                from='tester@localhost'
                to='you@google.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <node nodeId="Device33"/>
                </req>
            </iq>
            """)

        self.recv("""
            <iq type='result'
                from='you@google.com'
                to='tester@localhost'
                id='1'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='1'/>
            </iq>
            """)

        self.recv("""
            <message from='you@google.com'
                to='tester@localhost'>
                <failure xmlns='urn:xmpp:iot:sensordata' seqnr='1' done='true'>
                    <error nodeId='Device33' timestamp='2013-03-07T17:13:30'>Timeout.</error>
                </failure>
            </message>
            """)

        t1.join()
        time.sleep(.5)

        self.failUnlessEqual(results, ["accepted","failure"])
        # self.assertIn("nodeId", callback_data);
        self.assertTrue("nodeId" in callback_data)
        self.failUnlessEqual(callback_data["nodeId"], "Device33")
        # self.assertIn("timestamp", callback_data);
        self.assertTrue("timestamp" in callback_data)
        self.failUnlessEqual(callback_data["timestamp"], "2013-03-07T17:13:30")
        # self.assertIn("error_msg", callback_data);
        self.assertTrue("error_msg" in callback_data)
        self.failUnlessEqual(callback_data["error_msg"], "Timeout.")

    def testDelayedRequest(self):
        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0323'])

        myDevice = Device("Device22")
        myDevice._add_field(name="Temperature", typename="numeric", unit="°C")
        myDevice._set_momentary_timestamp("2013-03-07T16:24:30")
        myDevice._add_field_momentary_data("Temperature", "23.4", flags={"automaticReadout": "true"})

        self.xmpp['xep_0323'].register_node(nodeId="Device22", device=myDevice, commTimeout=0.5)

        dtnow = datetime.datetime.now()
        ts_2sec = datetime.timedelta(0,2)
        dtnow_plus_2sec = dtnow + ts_2sec
        when_flag = dtnow_plus_2sec.replace(microsecond=0).isoformat()

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1' momentary='true' when='""" + when_flag + """'/>
            </iq>
        """)

        self.send("""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='1'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='1' queued='true' />
            </iq>
            """)

        time.sleep(2)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <started xmlns='urn:xmpp:iot:sensordata' seqnr='1' />
            </message>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='1' done='true'>
                    <node nodeId='Device22'>
                        <timestamp value='2013-03-07T16:24:30'>
                            <numeric name='Temperature' momentary='true' automaticReadout='true' value='23.4' unit='°C'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
            """)

    def testDelayedRequestFail(self):
        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0323'])

        myDevice = Device("Device22")
        myDevice._add_field(name="Temperature", typename="numeric", unit="°C")
        myDevice._set_momentary_timestamp("2013-03-07T16:24:30")
        myDevice._add_field_momentary_data("Temperature", "23.4", flags={"automaticReadout": "true"})

        self.xmpp['xep_0323'].register_node(nodeId="Device22", device=myDevice, commTimeout=0.5)

        dtnow = datetime.datetime.now()
        ts_2sec = datetime.timedelta(0,2)
        dtnow_minus_2sec = dtnow - ts_2sec
        when_flag = dtnow_minus_2sec.replace(microsecond=0).isoformat()

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1' momentary='true' when='""" + when_flag + """'/>
            </iq>
        """)

        # Remove the returned datetime to allow predictable test
        xml_stanza = self._filtered_stanza_prepare()
        error_text = xml_stanza['rejected']['error'] #['text']
        error_text = error_text[:error_text.find(':')]
        xml_stanza['rejected']['error'] = error_text

        self._filtered_stanza_check("""
            <iq type='error'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='1'>
                <rejected xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <error>Invalid datetime in 'when' flag, cannot set a time in the past. Current time</error>
                </rejected>
            </iq>
            """, xml_stanza)


    def _filtered_stanza_prepare(self, timeout=.5):
        sent = self.xmpp.socket.next_sent(timeout)
        if sent is None:
            self.fail("No stanza was sent.")

        xml = self.parse_xml(sent)
        self.fix_namespaces(xml, 'jabber:client')
        sent = self.xmpp._build_stanza(xml, 'jabber:client')
        return sent

    def _filtered_stanza_check(self, data, filtered, defaults=None, use_values=True, method='exact'):
        self.check(filtered, data,
                   method=method,
                   defaults=defaults,
                   use_values=use_values)

    def testRequestFieldFrom(self):

        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0323'])

        myDevice = Device("Device44")
        myDevice._add_field(name='Voltage', typename="numeric", unit="V")
        myDevice._add_field_timestamp_data(name="Voltage", value="230.1", timestamp="2000-01-01T00:01:02", flags={"invoiced": "true"})
        myDevice._add_field_timestamp_data(name="Voltage", value="230.2", timestamp="2000-02-01T00:01:02", flags={"invoiced": "true"})
        myDevice._add_field_timestamp_data(name="Voltage", value="230.3", timestamp="2000-03-01T00:01:02", flags={"invoiced": "true"})

        self.xmpp['xep_0323'].register_node('Device44', myDevice, commTimeout=0.5)

        print("."),

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='6'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='6' from='2000-01-02T00:00:01'>
                    <field name='Voltage'/>
                </req>
            </iq>
        """)

        self.send("""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='6'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='6'/>
            </iq>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='6'>
                    <node nodeId='Device44'>
                        <timestamp value='2000-02-01T00:01:02'>
                            <numeric name='Voltage' invoiced='true' value='230.2' unit='V'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='6'>
                    <node nodeId='Device44'>
                        <timestamp value='2000-03-01T00:01:02'>
                            <numeric name='Voltage' invoiced='true' value='230.3' unit='V'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='6' done='true'>
                </fields>
            </message>
            """)

    def testRequestFieldTo(self):

        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0323'])

        myDevice = Device("Device44")
        myDevice._add_field(name='Voltage', typename="numeric", unit="V")
        myDevice._add_field_timestamp_data(name="Voltage", value="230.1", timestamp="2000-01-01T00:01:02", flags={"invoiced": "true"})
        myDevice._add_field_timestamp_data(name="Voltage", value="230.2", timestamp="2000-02-01T00:01:02", flags={"invoiced": "true"})
        myDevice._add_field_timestamp_data(name="Voltage", value="230.3", timestamp="2000-03-01T00:01:02", flags={"invoiced": "true"})

        self.xmpp['xep_0323'].register_node('Device44', myDevice, commTimeout=0.5)

        print("."),

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='6'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='6' to='2000-02-02T00:00:01'>
                    <field name='Voltage'/>
                </req>
            </iq>
        """)

        self.send("""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='6'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='6'/>
            </iq>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='6'>
                    <node nodeId='Device44'>
                        <timestamp value='2000-01-01T00:01:02'>
                            <numeric name='Voltage' invoiced='true' value='230.1' unit='V'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='6'>
                    <node nodeId='Device44'>
                        <timestamp value='2000-02-01T00:01:02'>
                            <numeric name='Voltage' invoiced='true' value='230.2' unit='V'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='6' done='true'>
                </fields>
            </message>
            """)

    def testRequestFieldFromTo(self):

        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0323'])

        myDevice = Device("Device44")
        myDevice._add_field(name='Voltage', typename="numeric", unit="V")
        myDevice._add_field_timestamp_data(name="Voltage", value="230.1", timestamp="2000-01-01T00:01:02", flags={"invoiced": "true"})
        myDevice._add_field_timestamp_data(name="Voltage", value="230.2", timestamp="2000-02-01T00:01:02", flags={"invoiced": "true"})
        myDevice._add_field_timestamp_data(name="Voltage", value="230.3", timestamp="2000-03-01T00:01:02", flags={"invoiced": "true"})

        self.xmpp['xep_0323'].register_node('Device44', myDevice, commTimeout=0.5)

        print("."),

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='6'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='6' from='2000-01-01T00:01:03' to='2000-02-02T00:00:01'>
                    <field name='Voltage'/>
                </req>
            </iq>
        """)

        self.send("""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='6'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='6'/>
            </iq>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='6'>
                    <node nodeId='Device44'>
                        <timestamp value='2000-02-01T00:01:02'>
                            <numeric name='Voltage' invoiced='true' value='230.2' unit='V'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
            """)

        self.send("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='6' done='true'>
                </fields>
            </message>
            """)

    def testDelayedRequestClient(self):
        self.stream_start(mode='client',
                          plugins=['xep_0030',
                                   'xep_0323'])

        results = []
        callback_data = {}

        def my_callback(from_jid, result, nodeId=None, timestamp=None, fields=None, error_msg=None):
            results.append(result)
            if result == "fields":
                callback_data["nodeId"] = nodeId
                callback_data["timestamp"] = timestamp
                callback_data["error_msg"] = error_msg
                for f in fields:
                    callback_data["field_" + f['name']] = f

        t1= threading.Thread(name="request_data",
                         target=self.xmpp['xep_0323'].request_data,
                         kwargs={"from_jid": "tester@localhost",
                                    "to_jid": "you@google.com",
                                    "nodeIds": ['Device33'],
                                    "callback": my_callback})
        t1.start()
        #self.xmpp['xep_0323'].request_data(from_jid="tester@localhost", to_jid="you@google.com", nodeIds=['Device33'], callback=my_callback);

        self.send("""
            <iq type='get'
                from='tester@localhost'
                to='you@google.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <node nodeId="Device33"/>
                </req>
            </iq>
            """)

        self.recv("""
            <iq type='result'
                from='you@google.com'
                to='tester@localhost'
                id='1'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='1'  queued='true'/>
            </iq>
            """)

        self.recv("""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <started xmlns='urn:xmpp:iot:sensordata' seqnr='1' />
            </message>
            """)

        self.recv("""
            <message from='you@google.com'
                     to='tester@localhost'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <node nodeId='Device33'>
                        <timestamp value='2000-01-01T00:01:02'>
                            <numeric name='Voltage' invoiced='true' value='230.4' unit='V'/>
                            <boolean name='TestBool' value='true'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
            """)

        self.recv("""
            <message from='you@google.com'
                     to='tester@localhost'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='1' done='true'/>
            </message>
            """)

        t1.join()
        time.sleep(.5)

        self.failUnlessEqual(results, ["queued","started","fields","done"])
        # self.assertIn("nodeId", callback_data);
        self.assertTrue("nodeId" in callback_data)
        self.failUnlessEqual(callback_data["nodeId"], "Device33")
        # self.assertIn("timestamp", callback_data);
        self.assertTrue("timestamp" in callback_data)
        self.failUnlessEqual(callback_data["timestamp"], "2000-01-01T00:01:02")
        # self.assertIn("field_Voltage", callback_data);
        self.assertTrue("field_Voltage" in callback_data)
        self.failUnlessEqual(callback_data["field_Voltage"], {"name": "Voltage", "value": "230.4", "typename": "numeric", "unit": "V", "flags": {"invoiced": "true"}})
        # self.assertIn("field_TestBool", callback_data);
        self.assertTrue("field_TestBool" in callback_data)
        self.failUnlessEqual(callback_data["field_TestBool"], {"name": "TestBool", "value": "true", "typename": "boolean" })


    def testRequestFieldsCancelAPI(self):

        self.stream_start(mode='client',
                          plugins=['xep_0030',
                                   'xep_0323'])

        results = []

        def my_callback(from_jid, result, nodeId=None, timestamp=None, fields=None, error_msg=None):
            results.append(result)

        session = self.xmpp['xep_0323'].request_data(from_jid="tester@localhost", to_jid="you@google.com", nodeIds=['Device33'], callback=my_callback)

        self.send("""
            <iq type='get'
                from='tester@localhost'
                to='you@google.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <node nodeId="Device33"/>
                </req>
            </iq>
            """)

        self.recv("""
            <iq type='result'
                from='you@google.com'
                to='tester@localhost'
                id='1'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='1'/>
            </iq>
            """)

        self.xmpp['xep_0323'].cancel_request(session=session)

        self.send("""
            <iq type='get'
                from='tester@localhost'
                to='you@google.com'
                id='1'>
                <cancel xmlns='urn:xmpp:iot:sensordata' seqnr='1' />
            </iq>
            """)

        self.recv("""
            <iq type='result'
                from='tester@localhost'
                to='you@google.com'
                id='1'>
                <cancelled xmlns='urn:xmpp:iot:sensordata' seqnr='1' />
            </iq>
            """)

        time.sleep(.5)

        self.failUnlessEqual(results, ["accepted","cancelled"])

    def testDelayedRequestCancel(self):
        self.stream_start(mode='component',
                          plugins=['xep_0030',
                                   'xep_0323'])

        myDevice = Device("Device22")
        myDevice._add_field(name="Temperature", typename="numeric", unit="°C")
        myDevice._set_momentary_timestamp("2013-03-07T16:24:30")
        myDevice._add_field_momentary_data("Temperature", "23.4", flags={"automaticReadout": "true"})

        self.xmpp['xep_0323'].register_node(nodeId="Device22", device=myDevice, commTimeout=0.5)

        dtnow = datetime.datetime.now()
        ts_2sec = datetime.timedelta(0,2)
        dtnow_plus_2sec = dtnow + ts_2sec
        when_flag = dtnow_plus_2sec.replace(microsecond=0).isoformat()

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1' momentary='true' when='""" + when_flag + """'/>
            </iq>
        """)

        self.send("""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='1'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='1' queued='true' />
            </iq>
            """)

        self.recv("""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <cancel xmlns='urn:xmpp:iot:sensordata' seqnr='1' />
            </iq>
            """)

        self.send("""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='1'>
                <cancelled xmlns='urn:xmpp:iot:sensordata' seqnr='1' />
            </iq>
            """)

        # Test cancel of non-existing request
        self.recv("""
            <iq type='get'
                from='tester@localhost'
                to='you@google.com'
                id='1'>
                <cancel xmlns='urn:xmpp:iot:sensordata' seqnr='1' />
            </iq>
            """)

        self.send("""
            <iq type='error'
                from='you@google.com'
                to='tester@localhost'
                id='1'>
                <rejected xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <error>Cancel request received, no matching request is active.</error>
                </rejected>
            </iq>
            """)

        time.sleep(2)

        # Ensure we don't get anything after cancellation
        self.send(None)



suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamSensorData)

