from sleekxmpp.test import *
import sleekxmpp.plugins.xep_0004 as xep_0004
import sleekxmpp.plugins.stanza_pubsub as pubsub


class TestPubsubStanzas(SleekTest):

    def testAffiliations(self):
        "Testing iq/pubsub/affiliations/affiliation stanzas"
        iq = self.Iq()
        aff1 = pubsub.Affiliation()
        aff1['node'] = 'testnode'
        aff1['affiliation'] = 'owner'
        aff2 = pubsub.Affiliation()
        aff2['node'] = 'testnode2'
        aff2['affiliation'] = 'publisher'
        iq['pubsub']['affiliations'].append(aff1)
        iq['pubsub']['affiliations'].append(aff2)
        self.check(iq, """
          <iq id="0">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <affiliations>
                <affiliation node="testnode" affiliation="owner" />
                <affiliation node="testnode2" affiliation="publisher" />
              </affiliations>
            </pubsub>
          </iq>""")

    def testSubscriptions(self):
        "Testing iq/pubsub/subscriptions/subscription stanzas"
        iq = self.Iq()
        sub1 = pubsub.Subscription()
        sub1['node'] = 'testnode'
        sub1['jid'] = 'steve@myserver.tld/someresource'
        sub2 = pubsub.Subscription()
        sub2['node'] = 'testnode2'
        sub2['jid'] = 'boogers@bork.top/bill'
        sub2['subscription'] = 'subscribed'
        iq['pubsub']['subscriptions'].append(sub1)
        iq['pubsub']['subscriptions'].append(sub2)
        self.check(iq, """
          <iq id="0">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <subscriptions>
                <subscription node="testnode" jid="steve@myserver.tld/someresource" />
                <subscription node="testnode2" jid="boogers@bork.top/bill" subscription="subscribed" />
              </subscriptions>
            </pubsub>
          </iq>""")

    def testOptionalSettings(self):
        "Testing iq/pubsub/subscription/subscribe-options stanzas"
        iq = self.Iq()
        iq['pubsub']['subscription']['suboptions']['required'] = True
        iq['pubsub']['subscription']['node'] = 'testnode alsdkjfas'
        iq['pubsub']['subscription']['jid'] = "fritzy@netflint.net/sleekxmpp"
        iq['pubsub']['subscription']['subscription'] = 'unconfigured'
        self.check(iq, """
          <iq id="0">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <subscription node="testnode alsdkjfas" jid="fritzy@netflint.net/sleekxmpp" subscription="unconfigured">
              <subscribe-options>
                <required />
                </subscribe-options>
              </subscription>
            </pubsub>
          </iq>""")

    def testItems(self):
        "Testing iq/pubsub/items stanzas"
        iq = self.Iq()
        iq['pubsub']['items']['node'] = 'crap'
        payload = ET.fromstring("""
          <thinger xmlns="http://andyet.net/protocol/thinger" x="1" y='2'>
            <child1 />
            <child2 normandy='cheese' foo='bar' />
          </thinger>""")
        payload2 = ET.fromstring("""
          <thinger2 xmlns="http://andyet.net/protocol/thinger2" x="12" y='22'>
            <child12 />
            <child22 normandy='cheese2' foo='bar2' />
          </thinger2>""")
        item = pubsub.Item()
        item['id'] = 'asdf'
        item['payload'] = payload
        item2 = pubsub.Item()
        item2['id'] = 'asdf2'
        item2['payload'] = payload2
        iq['pubsub']['items'].append(item)
        iq['pubsub']['items'].append(item2)
        self.check(iq, """
          <iq id="0">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <items node="crap">
                <item id="asdf">
                  <thinger xmlns="http://andyet.net/protocol/thinger" y="2" x="1">
                    <child1 />
                    <child2 foo="bar" normandy="cheese" />
                  </thinger>
                </item>
                <item id="asdf2">
                  <thinger2 xmlns="http://andyet.net/protocol/thinger2" y="22" x="12">
                    <child12 />
                    <child22 foo="bar2" normandy="cheese2" />
                  </thinger2>
                </item>
              </items>
            </pubsub>
          </iq>""")

    def testCreate(self):
        "Testing iq/pubsub/create&configure stanzas"
        iq = self.Iq()
        iq['pubsub']['create']['node'] = 'mynode'
        iq['pubsub']['configure']['form'].addField('pubsub#title',
                                                   ftype='text-single',
                                                   value='This thing is awesome')
        self.check(iq, """
          <iq id="0">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <create node="mynode" />
                <configure>
                  <x xmlns="jabber:x:data" type="form">
                    <field var="pubsub#title" type="text-single">
                      <value>This thing is awesome</value>
                    </field>
                  </x>
                </configure>
              </pubsub>
            </iq>""")

    def testState(self):
        "Testing iq/psstate stanzas"
        iq = self.Iq()
        iq['psstate']['node']= 'mynode'
        iq['psstate']['item']= 'myitem'
        pl = ET.Element('{http://andyet.net/protocol/pubsubqueue}claimed')
        iq['psstate']['payload'] = pl
        self.check(iq, """
          <iq id="0">
            <state xmlns="http://jabber.org/protocol/psstate" node="mynode" item="myitem">
              <claimed xmlns="http://andyet.net/protocol/pubsubqueue" />
            </state>
          </iq>""")

    def testDefault(self):
        "Testing iq/pubsub_owner/default stanzas"
        iq = self.Iq()
        iq['pubsub_owner']['default']
        iq['pubsub_owner']['default']['node'] = 'mynode'
        iq['pubsub_owner']['default']['type'] = 'leaf'
        iq['pubsub_owner']['default']['form'].addField('pubsub#title',
                                                       ftype='text-single',
                                                       value='This thing is awesome')
        self.check(iq, """
	      <iq id="0">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <default node="mynode" type="leaf">
                <x xmlns="jabber:x:data" type="form">
                  <field var="pubsub#title" type="text-single">
                    <value>This thing is awesome</value>
                  </field>
                </x>
             </default>
           </pubsub>
         </iq>""", use_values=False)

    def testSubscribe(self):
        "testing iq/pubsub/subscribe stanzas"
        iq = self.Iq()
        iq['pubsub']['subscribe']['options']
        iq['pubsub']['subscribe']['node'] = 'cheese'
        iq['pubsub']['subscribe']['jid'] = 'fritzy@netflint.net/sleekxmpp'
        iq['pubsub']['subscribe']['options']['node'] = 'cheese'
        iq['pubsub']['subscribe']['options']['jid'] = 'fritzy@netflint.net/sleekxmpp'
        form = xep_0004.Form()
        form.addField('pubsub#title', ftype='text-single', value='this thing is awesome')
        iq['pubsub']['subscribe']['options']['options'] = form
        self.check(iq, """
        <iq id="0">
          <pubsub xmlns="http://jabber.org/protocol/pubsub">
            <subscribe node="cheese" jid="fritzy@netflint.net/sleekxmpp">
              <options node="cheese" jid="fritzy@netflint.net/sleekxmpp">
                <x xmlns="jabber:x:data" type="form">
                  <field var="pubsub#title" type="text-single">
                    <value>this thing is awesome</value>
                  </field>
                </x>
              </options>
            </subscribe>
          </pubsub>
        </iq>""", use_values=False)

    def testPublish(self):
        "Testing iq/pubsub/publish stanzas"
        iq = self.Iq()
        iq['pubsub']['publish']['node'] = 'thingers'
        payload = ET.fromstring("""
          <thinger xmlns="http://andyet.net/protocol/thinger" x="1" y='2'>
             <child1 />
             <child2 normandy='cheese' foo='bar' />
           </thinger>""")
        payload2 = ET.fromstring("""
          <thinger2 xmlns="http://andyet.net/protocol/thinger2" x="12" y='22'>
            <child12 />
            <child22 normandy='cheese2' foo='bar2' />
           </thinger2>""")
        item = pubsub.Item()
        item['id'] = 'asdf'
        item['payload'] = payload
        item2 = pubsub.Item()
        item2['id'] = 'asdf2'
        item2['payload'] = payload2
        iq['pubsub']['publish'].append(item)
        iq['pubsub']['publish'].append(item2)

        self.check(iq, """
          <iq id="0">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <publish node="thingers">
                <item id="asdf">
                  <thinger xmlns="http://andyet.net/protocol/thinger" y="2" x="1">
                    <child1 />
                    <child2 foo="bar" normandy="cheese" />
                  </thinger>
                </item>
                <item id="asdf2">
                  <thinger2 xmlns="http://andyet.net/protocol/thinger2" y="22" x="12">
                    <child12 />
                    <child22 foo="bar2" normandy="cheese2" />
                  </thinger2>
                </item>
              </publish>
            </pubsub>
          </iq>""")

    def testDelete(self):
        "Testing iq/pubsub_owner/delete stanzas"
        iq = self.Iq()
        iq['pubsub_owner']['delete']['node'] = 'thingers'
        self.check(iq, """
          <iq id="0">
            <pubsub xmlns="http://jabber.org/protocol/pubsub#owner">
              <delete node="thingers" />
            </pubsub>
          </iq>""")

    def testCreateConfigGet(self):
        """Testing getting config from full create"""
        iq = self.Iq()
        iq['to'] = 'pubsub.asdf'
        iq['from'] = 'fritzy@asdf/87292ede-524d-4117-9076-d934ed3db8e7'
        iq['type'] = 'set'
        iq['id'] = 'E'

        pub = iq['pubsub']
        pub['create']['node'] = 'testnode2'
        pub['configure']['form']['type'] = 'submit'
        pub['configure']['form'].setFields([
                ('FORM_TYPE', {'type': 'hidden',
                               'value': 'http://jabber.org/protocol/pubsub#node_config'}),
                ('pubsub#node_type', {'type': 'list-single',
                                      'label': 'Select the node type',
                                      'value': 'leaf'}),
                ('pubsub#title', {'type': 'text-single',
                                  'label': 'A friendly name for the node'}),
                ('pubsub#deliver_notifications', {'type': 'boolean',
                                                  'label': 'Deliver event notifications',
                                                  'value': True}),
                ('pubsub#deliver_payloads', {'type': 'boolean',
                                             'label': 'Deliver payloads with event notifications',
                                             'value': True}),
                ('pubsub#notify_config', {'type': 'boolean',
                                          'label': 'Notify subscribers when the node configuration changes'}),
                ('pubsub#notify_delete', {'type': 'boolean',
                                          'label': 'Notify subscribers when the node is deleted'}),
                ('pubsub#notify_retract', {'type': 'boolean',
                                           'label': 'Notify subscribers when items are removed from the node',
                                           'value': True}),
                ('pubsub#notify_sub', {'type': 'boolean',
                                       'label': 'Notify owners about new subscribers and unsubscribes'}),
                ('pubsub#persist_items', {'type': 'boolean',
                                          'label': 'Persist items in storage'}),
                ('pubsub#max_items', {'type': 'text-single',
                                      'label': 'Max # of items to persist',
                                      'value': '10'}),
                ('pubsub#subscribe', {'type': 'boolean',
                                      'label': 'Whether to allow subscriptions',
                                      'value': True}),
                ('pubsub#access_model', {'type': 'list-single',
                                         'label': 'Specify the subscriber model',
                                         'value': 'open'}),
                ('pubsub#publish_model', {'type': 'list-single',
                                          'label': 'Specify the publisher model',
                                          'value': 'publishers'}),
                ('pubsub#send_last_published_item', {'type': 'list-single',
                                                     'label': 'Send last published item',
                                                     'value': 'never'}),
                ('pubsub#presence_based_delivery', {'type': 'boolean',
                                                    'label': 'Deliver notification only to available users'}),
                ])

        self.check(iq, """
          <iq to="pubsub.asdf" type="set" id="E" from="fritzy@asdf/87292ede-524d-4117-9076-d934ed3db8e7">
            <pubsub xmlns="http://jabber.org/protocol/pubsub">
              <create node="testnode2" />
              <configure>
                <x xmlns="jabber:x:data" type="submit">
                  <field var="FORM_TYPE" type="hidden">
                    <value>http://jabber.org/protocol/pubsub#node_config</value>
                  </field>
                  <field var="pubsub#node_type" type="list-single" label="Select the node type">
                    <value>leaf</value>
                  </field>
                  <field var="pubsub#title" type="text-single" label="A friendly name for the node" />
                  <field var="pubsub#deliver_notifications" type="boolean" label="Deliver event notifications">
                    <value>1</value>
                  </field>
                  <field var="pubsub#deliver_payloads" type="boolean" label="Deliver payloads with event notifications">
                    <value>1</value>
                  </field>
                  <field var="pubsub#notify_config" type="boolean" label="Notify subscribers when the node configuration changes" />
                  <field var="pubsub#notify_delete" type="boolean" label="Notify subscribers when the node is deleted" />
                  <field var="pubsub#notify_retract" type="boolean" label="Notify subscribers when items are removed from the node">
                    <value>1</value>
                  </field>
                  <field var="pubsub#notify_sub" type="boolean" label="Notify owners about new subscribers and unsubscribes" />
                  <field var="pubsub#persist_items" type="boolean" label="Persist items in storage" />
                  <field var="pubsub#max_items" type="text-single" label="Max # of items to persist">
                    <value>10</value>
                  </field>
                  <field var="pubsub#subscribe" type="boolean" label="Whether to allow subscriptions">
                    <value>1</value>
                  </field>
                  <field var="pubsub#access_model" type="list-single" label="Specify the subscriber model">
                    <value>open</value>
                  </field>
                  <field var="pubsub#publish_model" type="list-single" label="Specify the publisher model">
                    <value>publishers</value>
                  </field>
                  <field var="pubsub#send_last_published_item" type="list-single" label="Send last published item">
                    <value>never</value>
                  </field>
                  <field var="pubsub#presence_based_delivery" type="boolean" label="Deliver notification only to available users" />
                </x>
              </configure>
            </pubsub>
          </iq>""")

    def testItemEvent(self):
        """Testing message/pubsub_event/items/item"""
        msg = self.Message()
        item = pubsub.EventItem()
        pl = ET.Element('{http://netflint.net/protocol/test}test', {'failed':'3', 'passed':'24'})
        item['payload'] = pl
        item['id'] = 'abc123'
        msg['pubsub_event']['items'].append(item)
        msg['pubsub_event']['items']['node'] = 'cheese'
        msg['type'] = 'normal'
        self.check(msg, """
          <message type="normal">
            <event xmlns="http://jabber.org/protocol/pubsub#event">
              <items node="cheese">
                <item id="abc123">
                  <test xmlns="http://netflint.net/protocol/test" failed="3" passed="24" />
                </item>
              </items>
            </event>
          </message>""")

    def testItemsEvent(self):
        """Testing multiple message/pubsub_event/items/item"""
        msg = self.Message()
        item = pubsub.EventItem()
        item2 = pubsub.EventItem()
        pl = ET.Element('{http://netflint.net/protocol/test}test', {'failed':'3', 'passed':'24'})
        pl2 = ET.Element('{http://netflint.net/protocol/test-other}test', {'total':'27', 'failed':'3'})
        item2['payload'] = pl2
        item['payload'] = pl
        item['id'] = 'abc123'
        item2['id'] = '123abc'
        msg['pubsub_event']['items'].append(item)
        msg['pubsub_event']['items'].append(item2)
        msg['pubsub_event']['items']['node'] = 'cheese'
        msg['type'] = 'normal'
        self.check(msg, """
          <message type="normal">
            <event xmlns="http://jabber.org/protocol/pubsub#event">
              <items node="cheese">
                <item id="abc123">
                  <test xmlns="http://netflint.net/protocol/test" failed="3" passed="24" />
                </item>
                <item id="123abc">
                  <test xmlns="http://netflint.net/protocol/test-other" failed="3" total="27" />
                </item>
              </items>
            </event>
          </message>""")

    def testItemsEvent(self):
        """Testing message/pubsub_event/items/item & retract mix"""
        msg = self.Message()
        item = pubsub.EventItem()
        item2 = pubsub.EventItem()
        pl = ET.Element('{http://netflint.net/protocol/test}test', {'failed':'3', 'passed':'24'})
        pl2 = ET.Element('{http://netflint.net/protocol/test-other}test', {'total':'27', 'failed':'3'})
        item2['payload'] = pl2
        retract = pubsub.EventRetract()
        retract['id'] = 'aabbcc'
        item['payload'] = pl
        item['id'] = 'abc123'
        item2['id'] = '123abc'
        msg['pubsub_event']['items'].append(item)
        msg['pubsub_event']['items'].append(retract)
        msg['pubsub_event']['items'].append(item2)
        msg['pubsub_event']['items']['node'] = 'cheese'
        msg['type'] = 'normal'
        self.check(msg, """
          <message type="normal">
            <event xmlns="http://jabber.org/protocol/pubsub#event">
              <items node="cheese">
                <item id="abc123">
                  <test xmlns="http://netflint.net/protocol/test" failed="3" passed="24" />
                </item><retract id="aabbcc" />
                <item id="123abc">
                  <test xmlns="http://netflint.net/protocol/test-other" failed="3" total="27" />
                </item>
              </items>
            </event>
          </message>""")

    def testCollectionAssociate(self):
        """Testing message/pubsub_event/collection/associate"""
        msg = self.Message()
        msg['pubsub_event']['collection']['associate']['node'] = 'cheese'
        msg['pubsub_event']['collection']['node'] = 'cheeseburger'
        msg['type'] = 'headline'
        self.check(msg, """
          <message type="headline">
            <event xmlns="http://jabber.org/protocol/pubsub#event">
              <collection node="cheeseburger">
                <associate node="cheese" />
              </collection>
            </event>
          </message>""")

    def testCollectionDisassociate(self):
        """Testing message/pubsub_event/collection/disassociate"""
        msg = self.Message()
        msg['pubsub_event']['collection']['disassociate']['node'] = 'cheese'
        msg['pubsub_event']['collection']['node'] = 'cheeseburger'
        msg['type'] = 'headline'
        self.check(msg, """
          <message type="headline">
            <event xmlns="http://jabber.org/protocol/pubsub#event">
              <collection node="cheeseburger">
                <disassociate node="cheese" />
              </collection>
            </event>
          </message>""")

    def testEventConfiguration(self):
        """Testing message/pubsub_event/configuration/config"""
        msg = self.Message()
        msg['pubsub_event']['configuration']['node'] = 'cheese'
        msg['pubsub_event']['configuration']['form'].addField('pubsub#title',
                                                              ftype='text-single',
                                                              value='This thing is awesome')
        msg['type'] = 'headline'
        self.check(msg, """
        <message type="headline">
            <event xmlns="http://jabber.org/protocol/pubsub#event">
              <configuration node="cheese">
                <x xmlns="jabber:x:data" type="form">
                  <field var="pubsub#title" type="text-single">
                    <value>This thing is awesome</value>
                  </field>
                </x>
              </configuration>
            </event>
          </message>""")

    def testEventPurge(self):
        """Testing message/pubsub_event/purge"""
        msg = self.Message()
        msg['pubsub_event']['purge']['node'] = 'pickles'
        msg['type'] = 'headline'
        self.check(msg, """
          <message type="headline">
            <event xmlns="http://jabber.org/protocol/pubsub#event">
              <purge node="pickles" />
            </event>
          </message>""")

    def testEventSubscription(self):
        """Testing message/pubsub_event/subscription"""
        msg = self.Message()
        msg['pubsub_event']['subscription']['node'] = 'pickles'
        msg['pubsub_event']['subscription']['jid'] = 'fritzy@netflint.net/test'
        msg['pubsub_event']['subscription']['subid'] = 'aabb1122'
        msg['pubsub_event']['subscription']['subscription'] = 'subscribed'
        msg['pubsub_event']['subscription']['expiry'] = 'presence'
        msg['type'] = 'headline'
        self.check(msg, """
          <message type="headline">
            <event xmlns="http://jabber.org/protocol/pubsub#event">
              <subscription node="pickles" subid="aabb1122" jid="fritzy@netflint.net/test" subscription="subscribed" expiry="presence" />
            </event>
          </message>""")

suite = unittest.TestLoader().loadTestsFromTestCase(TestPubsubStanzas)
