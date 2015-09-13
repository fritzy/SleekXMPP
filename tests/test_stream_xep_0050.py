import time
import logging

import unittest
from sleekxmpp.test import SleekTest
from sleekxmpp.xmlstream import ElementBase, register_stanza_plugin


class TestAdHocCommands(SleekTest):

    def setUp(self):
        self.stream_start(mode='client',
                          plugins=['xep_0030', 'xep_0004', 'xep_0050'])

        # Real session IDs don't make for nice tests, so use
        # a dummy value.
        self.xmpp['xep_0050'].new_session = lambda: '_sessionid_'

    def tearDown(self):
        self.stream_close()

    def testInitialPayloadCommand(self):
        """Test a command with an initial payload."""

        class TestPayload(ElementBase):
            name = 'foo'
            namespace = 'test'
            interfaces = set(['bar'])
            plugin_attrib = name

        Command = self.xmpp['xep_0050'].stanza.Command
        register_stanza_plugin(Command, TestPayload, iterable=True)

        def handle_command(iq, session):
            initial = session['payload']
            logging.debug(initial)
            new_payload = TestPayload()
            if initial:
                new_payload['bar'] = 'Received: %s' % initial['bar']
            else:
                new_payload['bar'] = 'Failed'

            logging.debug(initial)

            session['payload'] = new_payload
            session['next'] = None
            session['has_next'] = False

            return session

        self.xmpp['xep_0050'].add_command('tester@localhost', 'foo',
                                          'Do Foo', handle_command)

        self.recv("""
          <iq id="11" type="set" to="tester@localhost" from="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     action="execute">
              <foo xmlns="test" bar="baz" />
            </command>
          </iq>
        """)

        self.send("""
          <iq id="11" type="result" to="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     status="completed"
                     sessionid="_sessionid_">
              <foo xmlns="test" bar="Received: baz" />
            </command>
          </iq>
        """)

    def testZeroStepCommand(self):
        """Test running a command with no steps."""

        def handle_command(iq, session):
            form = self.xmpp['xep_0004'].makeForm(ftype='result')
            form.addField(var='foo', ftype='text-single',
                          label='Foo', value='bar')

            session['payload'] = form
            session['next'] = None
            session['has_next'] = False

            return session

        self.xmpp['xep_0050'].add_command('tester@localhost', 'foo',
                                          'Do Foo', handle_command)

        self.recv("""
          <iq id="11" type="set" to="tester@localhost" from="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     action="execute" />
          </iq>
        """)

        self.send("""
          <iq id="11" type="result" to="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     status="completed"
                     sessionid="_sessionid_">
              <x xmlns="jabber:x:data" type="result">
                <field var="foo" label="Foo" type="text-single">
                  <value>bar</value>
                </field>
              </x>
            </command>
          </iq>
        """)

    def testOneStepCommand(self):
        """Test running a single step command."""
        results = []

        def handle_command(iq, session):

            def handle_form(form, session):
                results.append(form['values']['foo'])
                session['payload'] = None

            form = self.xmpp['xep_0004'].makeForm('form')
            form.addField(var='foo', ftype='text-single', label='Foo')

            session['payload'] = form
            session['next'] = handle_form
            session['has_next'] = False

            return session

        self.xmpp['xep_0050'].add_command('tester@localhost', 'foo',
                                          'Do Foo', handle_command)

        self.recv("""
          <iq id="11" type="set" to="tester@localhost" from="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     action="execute" />
          </iq>
        """)

        self.send("""
          <iq id="11" type="result" to="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     status="executing"
                     sessionid="_sessionid_">
              <actions>
                <complete />
              </actions>
              <x xmlns="jabber:x:data" type="form">
                <field var="foo" label="Foo" type="text-single" />
              </x>
            </command>
          </iq>
        """)

        self.recv("""
          <iq id="12" type="set" to="tester@localhost" from="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     action="complete"
                     sessionid="_sessionid_">
              <x xmlns="jabber:x:data" type="submit">
                <field var="foo" label="Foo" type="text-single">
                  <value>blah</value>
                </field>
              </x>
            </command>
          </iq>
        """)

        self.send("""
          <iq id="12" type="result" to="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     status="completed"
                     sessionid="_sessionid_" />
          </iq>
        """)

        self.assertEqual(results, ['blah'],
                "Command handler was not executed: %s" % results)

    def testTwoStepCommand(self):
        """Test using a two-stage command."""
        results = []

        def handle_command(iq, session):

            def handle_step2(form, session):
                results.append(form['values']['bar'])
                session['payload'] = None

            def handle_step1(form, session):
                results.append(form['values']['foo'])

                form = self.xmpp['xep_0004'].makeForm('form')
                form.addField(var='bar', ftype='text-single', label='Bar')

                session['payload'] = form
                session['next'] = handle_step2
                session['has_next'] = False

                return session

            form = self.xmpp['xep_0004'].makeForm('form')
            form.addField(var='foo', ftype='text-single', label='Foo')

            session['payload'] = form
            session['next'] = handle_step1
            session['has_next'] = True

            return session

        self.xmpp['xep_0050'].add_command('tester@localhost', 'foo',
                                          'Do Foo', handle_command)

        self.recv("""
          <iq id="11" type="set" to="tester@localhost" from="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     action="execute" />
          </iq>
        """)

        self.send("""
          <iq id="11" type="result" to="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     status="executing"
                     sessionid="_sessionid_">
              <actions>
                <next />
              </actions>
              <x xmlns="jabber:x:data" type="form">
                <field var="foo" label="Foo" type="text-single" />
              </x>
            </command>
          </iq>
        """)

        self.recv("""
          <iq id="12" type="set" to="tester@localhost" from="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     action="next"
                     sessionid="_sessionid_">
              <x xmlns="jabber:x:data" type="submit">
                <field var="foo" label="Foo" type="text-single">
                  <value>blah</value>
                </field>
              </x>
            </command>
          </iq>
        """)

        self.send("""
          <iq id="12" type="result" to="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     status="executing"
                     sessionid="_sessionid_">
              <actions>
                <complete />
              </actions>
              <x xmlns="jabber:x:data" type="form">
                <field var="bar" label="Bar" type="text-single" />
              </x>
            </command>
          </iq>
        """)

        self.recv("""
          <iq id="13" type="set" to="tester@localhost" from="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     action="complete"
                     sessionid="_sessionid_">
              <x xmlns="jabber:x:data" type="submit">
                <field var="bar" label="Bar" type="text-single">
                  <value>meh</value>
                </field>
              </x>
            </command>
          </iq>
        """)
        self.send("""
          <iq id="13" type="result" to="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     status="completed"
                     sessionid="_sessionid_" />
          </iq>
        """)

        self.assertEqual(results, ['blah', 'meh'],
                "Command handler was not executed: %s" % results)

    def testCancelCommand(self):
        """Test canceling command."""
        results = []

        def handle_command(iq, session):

            def handle_form(form, session):
                results.append(form['values']['foo'])

            def handle_cancel(iq, session):
                results.append('canceled')

            form = self.xmpp['xep_0004'].makeForm('form')
            form.addField(var='foo', ftype='text-single', label='Foo')

            session['payload'] = form
            session['next'] = handle_form
            session['cancel'] = handle_cancel
            session['has_next'] = False

            return session

        self.xmpp['xep_0050'].add_command('tester@localhost', 'foo',
                                          'Do Foo', handle_command)

        self.recv("""
          <iq id="11" type="set" to="tester@localhost" from="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     action="execute" />
          </iq>
        """)

        self.send("""
          <iq id="11" type="result" to="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     status="executing"
                     sessionid="_sessionid_">
              <actions>
                <complete />
              </actions>
              <x xmlns="jabber:x:data" type="form">
                <field var="foo" label="Foo" type="text-single" />
              </x>
            </command>
          </iq>
        """)

        self.recv("""
          <iq id="12" type="set" to="tester@localhost" from="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     action="cancel"
                     sessionid="_sessionid_">
              <x xmlns="jabber:x:data" type="submit">
                <field var="foo" label="Foo" type="text-single">
                  <value>blah</value>
                </field>
              </x>
            </command>
          </iq>
        """)

        self.send("""
          <iq id="12" type="result" to="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     status="canceled"
                     sessionid="_sessionid_" />
          </iq>
        """)

        self.assertEqual(results, ['canceled'],
                "Cancelation handler not executed: %s" % results)

    def testCommandNote(self):
        """Test adding notes to commands."""

        def handle_command(iq, session):
            form = self.xmpp['xep_0004'].makeForm(ftype='result')
            form.addField(var='foo', ftype='text-single',
                          label='Foo', value='bar')

            session['payload'] = form
            session['next'] = None
            session['has_next'] = False
            session['notes'] = [('info', 'testing notes')]

            return session

        self.xmpp['xep_0050'].add_command('tester@localhost', 'foo',
                                          'Do Foo', handle_command)

        self.recv("""
          <iq id="11" type="set" to="tester@localhost" from="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     action="execute" />
          </iq>
        """)

        self.send("""
          <iq id="11" type="result" to="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     status="completed"
                     sessionid="_sessionid_">
              <note type="info">testing notes</note>
              <x xmlns="jabber:x:data" type="result">
                <field var="foo" label="Foo" type="text-single">
                  <value>bar</value>
                </field>
              </x>
            </command>
          </iq>
        """)



    def testMultiPayloads(self):
        """Test using commands with multiple payloads."""
        results = []

        def handle_command(iq, session):

            def handle_form(forms, session):
                for form in forms:
                    results.append(form['values']['FORM_TYPE'])
                session['payload'] = None

            form1 = self.xmpp['xep_0004'].makeForm('form')
            form1.addField(var='FORM_TYPE', ftype='hidden', value='form_1')
            form1.addField(var='foo', ftype='text-single', label='Foo')

            form2 = self.xmpp['xep_0004'].makeForm('form')
            form2.addField(var='FORM_TYPE', ftype='hidden', value='form_2')
            form2.addField(var='foo', ftype='text-single', label='Foo')

            session['payload'] = [form1, form2]
            session['next'] = handle_form
            session['has_next'] = False

            return session

        self.xmpp['xep_0050'].add_command('tester@localhost', 'foo',
                                          'Do Foo', handle_command)

        self.recv("""
          <iq id="11" type="set" to="tester@localhost" from="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     action="execute" />
          </iq>
        """)

        self.send("""
          <iq id="11" type="result" to="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     status="executing"
                     sessionid="_sessionid_">
              <actions>
                <complete />
              </actions>
              <x xmlns="jabber:x:data" type="form">
                <field var="FORM_TYPE" type="hidden">
                  <value>form_1</value>
                </field>
                <field var="foo" label="Foo" type="text-single" />
              </x>
              <x xmlns="jabber:x:data" type="form">
                <field var="FORM_TYPE" type="hidden">
                  <value>form_2</value>
                </field>
                <field var="foo" label="Foo" type="text-single" />
              </x>
            </command>
          </iq>
        """)

        self.recv("""
          <iq id="12" type="set" to="tester@localhost" from="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     action="complete"
                     sessionid="_sessionid_">
             <x xmlns="jabber:x:data" type="submit">
                <field var="FORM_TYPE" type="hidden">
                  <value>form_1</value>
                </field>
                <field var="foo" type="text-single">
                  <value>bar</value>
                </field>
              </x>
              <x xmlns="jabber:x:data" type="submit">
                <field var="FORM_TYPE" type="hidden">
                  <value>form_2</value>
                </field>
                <field var="foo" type="text-single">
                  <value>bar</value>
                </field>
              </x>
            </command>
          </iq>
        """)

        self.send("""
          <iq id="12" type="result" to="foo@bar">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="foo"
                     status="completed"
                     sessionid="_sessionid_" />
          </iq>
        """)

        self.assertEqual(results, [['form_1'], ['form_2']],
                "Command handler was not executed: %s" % results)

    def testClientAPI(self):
        """Test using client-side API for commands."""
        results = []

        def handle_complete(iq, session):
            for item in session['custom_data']:
                results.append(item)

        def handle_step2(iq, session):
            form = self.xmpp['xep_0004'].makeForm(ftype='submit')
            form.addField(var='bar', value='123')

            session['custom_data'].append('baz')
            session['payload'] = form
            session['next'] = handle_complete
            self.xmpp['xep_0050'].complete_command(session)

        def handle_step1(iq, session):
            form = self.xmpp['xep_0004'].makeForm(ftype='submit')
            form.addField(var='foo', value='42')

            session['custom_data'].append('bar')
            session['payload'] = form
            session['next'] = handle_step2
            self.xmpp['xep_0050'].continue_command(session)

        session = {'custom_data': ['foo'],
                   'next': handle_step1}

        self.xmpp['xep_0050'].start_command(
                'foo@example.com',
                'test_client',
                session)

        self.send("""
          <iq id="1" to="foo@example.com" type="set">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="test_client"
                     action="execute" />
          </iq>
        """)

        self.recv("""
          <iq id="1" from="foo@example.com" type="result">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="test_client"
                     sessionid="_sessionid_"
                     status="executing">
              <x xmlns="jabber:x:data" type="form">
                <field var="foo" type="text-single" />
              </x>
            </command>
          </iq>
        """)

        self.send("""
          <iq id="2" to="foo@example.com" type="set">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="test_client"
                     sessionid="_sessionid_"
                     action="next">
              <x xmlns="jabber:x:data" type="submit">
                <field var="foo">
                  <value>42</value>
                </field>
              </x>
            </command>
          </iq>
        """)

        self.recv("""
          <iq id="2" from="foo@example.com" type="result">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="test_client"
                     sessionid="_sessionid_"
                     status="executing">
              <x xmlns="jabber:x:data" type="form">
                <field var="bar" type="text-single" />
              </x>
            </command>
          </iq>
        """)

        self.send("""
          <iq id="3" to="foo@example.com" type="set">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="test_client"
                     sessionid="_sessionid_"
                     action="complete">
              <x xmlns="jabber:x:data" type="submit">
                <field var="bar">
                  <value>123</value>
                </field>
              </x>
            </command>
          </iq>
        """)

        self.recv("""
          <iq id="3" from="foo@example.com" type="result">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="test_client"
                     sessionid="_sessionid_"
                     status="completed" />
          </iq>
        """)

        # Give the event queue time to process
        time.sleep(0.3)

        self.failUnless(results == ['foo', 'bar', 'baz'],
                'Incomplete command workflow: %s' % results)

    def testClientAPICancel(self):
        """Test using client-side cancel API for commands."""
        results = []

        def handle_canceled(iq, session):
            for item in session['custom_data']:
                results.append(item)

        def handle_step1(iq, session):
            session['custom_data'].append('bar')
            session['next'] = handle_canceled
            self.xmpp['xep_0050'].cancel_command(session)

        session = {'custom_data': ['foo'],
                   'next': handle_step1}

        self.xmpp['xep_0050'].start_command(
                'foo@example.com',
                'test_client',
                session)

        self.send("""
          <iq id="1" to="foo@example.com" type="set">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="test_client"
                     action="execute" />
          </iq>
        """)

        self.recv("""
          <iq id="1" to="foo@example.com" type="result">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="test_client"
                     sessionid="_sessionid_"
                     status="executing">
              <x xmlns="jabber:x:data" type="form">
                <field var="foo" type="text-single" />
              </x>
            </command>
          </iq>
        """)

        self.send("""
          <iq id="2" to="foo@example.com" type="set">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="test_client"
                     sessionid="_sessionid_"
                     action="cancel" />
          </iq>
        """)

        self.recv("""
          <iq id="2" to="foo@example.com" type="result">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="test_client"
                     sessionid="_sessionid_"
                     status="canceled" />
          </iq>
        """)

        # Give the event queue time to process
        time.sleep(0.3)

        self.failUnless(results == ['foo', 'bar'],
                'Incomplete command workflow: %s' % results)

    def testClientAPIError(self):
        """Test using client-side error API for commands."""
        results = []

        def handle_error(iq, session):
            for item in session['custom_data']:
                results.append(item)

        session = {'custom_data': ['foo'],
                   'error': handle_error}

        self.xmpp['xep_0050'].start_command(
                'foo@example.com',
                'test_client',
                session)

        self.send("""
          <iq id="1" to="foo@example.com" type="set">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="test_client"
                     action="execute" />
          </iq>
        """)

        self.recv("""
          <iq id="1" to="foo@example.com" type="error">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="test_client"
                     action="execute" />
            <error type='cancel'>
              <item-not-found xmlns='urn:ietf:params:xml:ns:xmpp-stanzas'/>
            </error>
          </iq>
        """)

        # Give the event queue time to process
        time.sleep(0.3)

        self.failUnless(results == ['foo'],
                'Incomplete command workflow: %s' % results)

    def testClientAPIErrorStrippedResponse(self):
        """Test errors that don't include the command substanza."""
        results = []

        def handle_error(iq, session):
            for item in session['custom_data']:
                results.append(item)

        session = {'custom_data': ['foo'],
                   'error': handle_error}

        self.xmpp['xep_0050'].start_command(
                'foo@example.com',
                'test_client',
                session)

        self.send("""
          <iq id="1" to="foo@example.com" type="set">
            <command xmlns="http://jabber.org/protocol/commands"
                     node="test_client"
                     action="execute" />
          </iq>
        """)

        self.recv("""
          <iq id="1" to="foo@example.com" type="error">
            <error type='cancel'>
              <item-not-found xmlns='urn:ietf:params:xml:ns:xmpp-stanzas' />
            </error>
          </iq>
        """)

        # Give the event queue time to process
        time.sleep(0.3)

        self.failUnless(results == ['foo'],
                'Incomplete command workflow: %s' % results)





suite = unittest.TestLoader().loadTestsFromTestCase(TestAdHocCommands)
