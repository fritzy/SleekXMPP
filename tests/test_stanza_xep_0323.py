# -*- coding: utf-8 -*-

from sleekxmpp.test import *
import sleekxmpp.plugins.xep_0323 as xep_0323

namespace='sn'

class TestSensorDataStanzas(SleekTest):


    def setUp(self):
        pass
        #register_stanza_plugin(Iq, xep_0323.stanza.Request)
        #register_stanza_plugin(Iq, xep_0323.stanza.Accepted)
        #register_stanza_plugin(Message, xep_0323.stanza.Failure)
        #register_stanza_plugin(xep_0323.stanza.Failure, xep_0323.stanza.Error)
        #register_stanza_plugin(Iq, xep_0323.stanza.Rejected)
        #register_stanza_plugin(Message, xep_0323.stanza.Fields)
        #register_stanza_plugin(Message, xep_0323.stanza.Request)
        #register_stanza_plugin(Message, xep_0323.stanza.Accepted)
        #register_stanza_plugin(Message, xep_0323.stanza.Failure)
        # register_stanza_plugin(Message, xep_0323.stanza.Result)
        # register_stanza_plugin(Message, xep_0323.stanza.Gone)
        # register_stanza_plugin(Message, xep_0323.stanza.Inactive)
        # register_stanza_plugin(Message, xep_0323.stanza.Paused)

    def testRequest(self):
        """
        test of request stanza
        """
        iq = self.Iq()
        iq['type'] = 'get'
        iq['from'] = 'master@clayster.com/amr'
        iq['to'] = 'device@clayster.com'
        iq['id'] = '1'
        iq['req']['seqnr'] = '1'
        iq['req']['momentary'] = 'true'

        self.check(iq,"""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1' momentary='true'/>
            </iq>
        """
            )

    def testRequestNodes(self):
        """
        test of request nodes stanza
        """
        iq = self.Iq()
        iq['type'] = 'get'
        iq['from'] = 'master@clayster.com/amr'
        iq['to'] = 'device@clayster.com'
        iq['id'] = '1'
        iq['req']['seqnr'] = '1'
        iq['req']['momentary'] = 'true'


        iq['req'].add_node("Device02", "Source02", "CacheType")
        iq['req'].add_node("Device44")

        self.check(iq,"""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1' momentary='true'>
                    <node nodeId='Device02' sourceId='Source02' cacheType='CacheType'/>
                    <node nodeId='Device44'/>
                </req>
            </iq>
        """
            )

        iq['req'].del_node("Device02")

        self.check(iq,"""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1' momentary='true'>
                    <node nodeId='Device44'/>
                </req>
            </iq>
        """
            )

        iq['req'].del_nodes()

        self.check(iq,"""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1' momentary='true'>
                </req>
            </iq>
        """
            )

    def testRequestField(self):
        """
        test of request field stanza
        """
        iq = self.Iq()
        iq['type'] = 'get'
        iq['from'] = 'master@clayster.com/amr'
        iq['to'] = 'device@clayster.com'
        iq['id'] = '1'
        iq['req']['seqnr'] = '1'
        iq['req']['momentary'] = 'true'


        iq['req'].add_field("Top temperature")
        iq['req'].add_field("Bottom temperature")

        self.check(iq,"""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1' momentary='true'>
                    <field name='Top temperature'/>
                    <field name='Bottom temperature'/>
                </req>
            </iq>
        """
            )

        iq['req'].del_field("Top temperature")

        self.check(iq,"""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1' momentary='true'>
                    <field name='Bottom temperature'/>
                </req>
            </iq>
        """
            )

        iq['req'].del_fields()

        self.check(iq,"""
            <iq type='get'
                from='master@clayster.com/amr'
                to='device@clayster.com'
                id='1'>
                <req xmlns='urn:xmpp:iot:sensordata' seqnr='1' momentary='true'>
                </req>
            </iq>
        """
            )


    def testAccepted(self):
        """
        test of request stanza
        """
        iq = self.Iq()
        iq['type'] = 'result'
        iq['from'] = 'device@clayster.com'
        iq['to'] = 'master@clayster.com/amr'
        iq['id'] = '2'
        iq['accepted']['seqnr'] = '2'

        self.check(iq,"""
            <iq type='result'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='2'>
                <accepted xmlns='urn:xmpp:iot:sensordata' seqnr='2'/>
            </iq>
        """
            )

    def testRejected(self):
        """
        test of request stanza
        """
        iq = self.Iq()
        iq['type'] = 'error'
        iq['from'] = 'device@clayster.com'
        iq['to'] = 'master@clayster.com/amr'
        iq['id'] = '4'
        iq['rejected']['seqnr'] = '4'
        iq['rejected']['error'] = 'Access denied.'

        self.check(iq,"""
            <iq type='error'
                from='device@clayster.com'
                to='master@clayster.com/amr'
                id='4'>
                <rejected xmlns='urn:xmpp:iot:sensordata' seqnr='4'>
                    <error>Access denied.</error>
                </rejected>
            </iq>
        """
            )

    def testFailure(self):
        """
        test of failure stanza
        """
        msg = self.Message()
        msg['from'] = 'device@clayster.com'
        msg['to'] = 'master@clayster.com/amr'
        msg['failure']['seqnr'] = '3'
        msg['failure']['done'] = 'true'
        msg['failure']['error']['nodeId'] = 'Device01'
        msg['failure']['error']['timestamp'] = '2013-03-07T17:13:30'
        msg['failure']['error']['text'] = 'Timeout.'

        self.check(msg,"""
            <message from='device@clayster.com'
                     to='master@clayster.com/amr'>
                <failure xmlns='urn:xmpp:iot:sensordata' seqnr='3' done='true'>
                    <error nodeId='Device01' timestamp='2013-03-07T17:13:30'>
                        Timeout.</error>
                </failure>
            </message>
        """
            )

    def testFields(self):
        """
        test of fields stanza
        """
        msg = self.Message()
        msg['from'] = 'device@clayster.com'
        msg['to'] = 'master@clayster.com/amr'
        msg['fields']['seqnr'] = '1'

        node = msg['fields'].add_node("Device02")
        ts = node.add_timestamp("2013-03-07T16:24:30")

        data = ts.add_data(typename="numeric", name="Temperature", value="-12.42", unit='K')
        data['momentary'] = 'true'
        data['automaticReadout'] = 'true'

        self.check(msg,"""
            <message from='device@clayster.com'
                    to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <node nodeId='Device02'>
                        <timestamp value='2013-03-07T16:24:30'>
                            <numeric name='Temperature' momentary='true' automaticReadout='true' value='-12.42' unit='K'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
                       """
            )

        node = msg['fields'].add_node("EmptyDevice")
        node = msg['fields'].add_node("Device04")
        ts = node.add_timestamp("EmptyTimestamp")

        self.check(msg,"""
            <message from='device@clayster.com'
                    to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <node nodeId='Device02'>
                        <timestamp value='2013-03-07T16:24:30'>
                            <numeric name='Temperature' momentary='true' automaticReadout='true' value='-12.42' unit='K'/>
                        </timestamp>
                    </node>
                    <node nodeId='EmptyDevice'/>
                    <node nodeId='Device04'>
                        <timestamp value='EmptyTimestamp'/>
                    </node>
                </fields>
            </message>
                       """
            )

        node = msg['fields'].add_node("Device77")
        ts = node.add_timestamp("2013-05-03T12:00:01")
        data = ts.add_data(typename="numeric", name="Temperature", value="-12.42", unit='K')
        data['historicalDay'] = 'true'
        data = ts.add_data(typename="numeric", name="Speed", value="312.42", unit='km/h')
        data['historicalWeek'] = 'false'
        data = ts.add_data(typename="string", name="Temperature name", value="Bottom oil")
        data['historicalMonth'] = 'true'
        data = ts.add_data(typename="string", name="Speed name", value="Top speed")
        data['historicalQuarter'] = 'false'
        data = ts.add_data(typename="dateTime", name="T1", value="1979-01-01T00:00:00")
        data['historicalYear'] = 'true'
        data = ts.add_data(typename="dateTime", name="T2", value="2000-01-01T01:02:03")
        data['historicalOther'] = 'false'
        data = ts.add_data(typename="timeSpan", name="TS1", value="P5Y")
        data['missing'] = 'true'
        data = ts.add_data(typename="timeSpan", name="TS2", value="PT2M1S")
        data['manualEstimate'] = 'false'
        data = ts.add_data(typename="enum", name="top color", value="red", dataType="string")
        data['invoiced'] = 'true'
        data = ts.add_data(typename="enum", name="bottom color", value="black", dataType="string")
        data['powerFailure'] = 'false'
        data = ts.add_data(typename="boolean", name="Temperature real", value="false")
        data['historicalDay'] = 'true'
        data = ts.add_data(typename="boolean", name="Speed real", value="true")
        data['historicalWeek'] = 'false'

        self.check(msg,"""
            <message from='device@clayster.com'
                    to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <node nodeId='Device02'>
                        <timestamp value='2013-03-07T16:24:30'>
                            <numeric name='Temperature' momentary='true' automaticReadout='true' value='-12.42' unit='K'/>
                        </timestamp>
                    </node>
                    <node nodeId='EmptyDevice'/>
                    <node nodeId='Device04'>
                        <timestamp value='EmptyTimestamp'/>
                    </node>
                    <node nodeId='Device77'>
                        <timestamp value='2013-05-03T12:00:01'>
                            <numeric name='Temperature' historicalDay='true' value='-12.42' unit='K'/>
                            <numeric name='Speed' historicalWeek='false' value='312.42' unit='km/h'/>
                            <string name='Temperature name' historicalMonth='true' value='Bottom oil'/>
                            <string name='Speed name' historicalQuarter='false' value='Top speed'/>
                            <dateTime name='T1' historicalYear='true' value='1979-01-01T00:00:00'/>
                            <dateTime name='T2' historicalOther='false' value='2000-01-01T01:02:03'/>
                            <timeSpan name='TS1' missing='true' value='P5Y'/>
                            <timeSpan name='TS2' manualEstimate='false' value='PT2M1S'/>
                            <enum name='top color' invoiced='true' value='red' dataType='string'/>
                            <enum name='bottom color' powerFailure='false' value='black' dataType='string'/>
                            <boolean name='Temperature real' historicalDay='true' value='false'/>
                            <boolean name='Speed real' historicalWeek='false' value='true'/>
                        </timestamp>
                    </node>
                </fields>
            </message>
                       """
            )


    def testTimestamp(self):
        msg = self.Message()

        msg['from'] = 'device@clayster.com'
        msg['to'] = 'master@clayster.com/amr'
        msg['fields']['seqnr'] = '1'

        node = msg['fields'].add_node("Device02")
        node = msg['fields'].add_node("Device03")

        ts = node.add_timestamp("2013-03-07T16:24:30")
        ts = node.add_timestamp("2013-03-07T16:24:31")

        self.check(msg,"""
            <message from='device@clayster.com'
                    to='master@clayster.com/amr'>
                <fields xmlns='urn:xmpp:iot:sensordata' seqnr='1'>
                    <node nodeId='Device02'/>
                    <node nodeId='Device03'>
                        <timestamp value='2013-03-07T16:24:30'/>
                        <timestamp value='2013-03-07T16:24:31'/>
                    </node>
                </fields>
            </message>
                       """
            )


    def testStringIdsMatcher(self):
        """
        test of StringIds follow spec
        """
        emptyStringIdXML='<message xmlns="jabber:client"><fields xmlns="urn:xmpp:iot:sensordata" /></message>'

        msg = self.Message()
        msg['fields']['stringIds'] = "Nisse"
        self.check(msg,emptyStringIdXML)
        msg['fields']['stringIds'] = "Nisse___nje#"
        self.check(msg,emptyStringIdXML)
        msg['fields']['stringIds'] = "1"
        self.check(msg,emptyStringIdXML)




suite = unittest.TestLoader().loadTestsFromTestCase(TestSensorDataStanzas)
