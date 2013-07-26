from sleekxmpp.xmlstream.matcher import MatchXPath
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.exceptions import XMPPError
import unittest
from sleekxmpp.test import SleekTest


class TestStreamExceptions(SleekTest):
    """
    Test handling roster updates.
    """

    def tearDown(self):
        self.stream_close()

    def testExceptionReply(self):
        """Test that raising an exception replies with the original stanza."""

        def message(msg):
            msg.reply()
            msg['body'] = 'Body changed'
            raise XMPPError(clear=False)

        self.stream_start()
        self.xmpp.add_event_handler('message', message)

        self.recv("""
          <message>
            <body>This is going to cause an error.</body>
          </message>
        """)

        self.send("""
          <message type="error">
            <body>This is going to cause an error.</body>
            <error type="cancel" code="500">
              <undefined-condition
                  xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
            </error>
          </message>
        """)

    def testExceptionContinueWorking(self):
        """Test that Sleek continues to respond after an XMPPError is raised."""

        def message(msg):
            msg.reply()
            msg['body'] = 'Body changed'
            raise XMPPError(clear=False)

        self.stream_start()
        self.xmpp.add_event_handler('message', message)

        self.recv("""
          <message>
            <body>This is going to cause an error.</body>
          </message>
        """)

        self.send("""
          <message type="error">
            <body>This is going to cause an error.</body>
            <error type="cancel" code="500">
              <undefined-condition
                  xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
            </error>
          </message>
        """)

        self.recv("""
          <message>
            <body>This is going to cause an error.</body>
          </message>
        """)

        self.send("""
          <message type="error">
            <body>This is going to cause an error.</body>
            <error type="cancel" code="500">
              <undefined-condition
                  xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
            </error>
          </message>
        """)

    def testXMPPErrorException(self):
        """Test raising an XMPPError exception."""

        def message(msg):
            raise XMPPError(condition='feature-not-implemented',
                            text="We don't do things that way here.",
                            etype='cancel',
                            extension='foo',
                            extension_ns='foo:error',
                            extension_args={'test': 'true'})

        self.stream_start()
        self.xmpp.add_event_handler('message', message)

        self.recv("""
          <message>
            <body>This is going to cause an error.</body>
          </message>
        """)

        self.send("""
          <message type="error">
            <error type="cancel" code="501">
              <feature-not-implemented
                  xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
              <text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">
                We don&apos;t do things that way here.
              </text>
              <foo xmlns="foo:error" test="true" />
            </error>
          </message>
        """, use_values=False)

    def testIqErrorException(self):
        """Test using error exceptions with Iq stanzas."""

        def handle_iq(iq):
            raise XMPPError(condition='feature-not-implemented',
                            text="We don't do things that way here.",
                            etype='cancel',
                            clear=False)

        self.stream_start()
        self.xmpp.register_handler(
                Callback(
                    'Test Iq',
                     MatchXPath('{%s}iq/{test}query' % self.xmpp.default_ns),
                     handle_iq))

        self.recv("""
          <iq type="get" id="0">
            <query xmlns="test" />
          </iq>
        """)

        self.send("""
          <iq type="error" id="0">
            <query xmlns="test" />
            <error type="cancel" code="501">
              <feature-not-implemented
                  xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
              <text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">
                We don&apos;t do things that way here.
              </text>
            </error>
          </iq>
        """, use_values=False)

    def testThreadedXMPPErrorException(self):
        """Test raising an XMPPError exception in a threaded handler."""

        def message(msg):
            raise XMPPError(condition='feature-not-implemented',
                            text="We don't do things that way here.",
                            etype='cancel')

        self.stream_start()
        self.xmpp.add_event_handler('message', message,
                                    threaded=True)

        self.recv("""
          <message>
            <body>This is going to cause an error.</body>
          </message>
        """)

        self.send("""
          <message type="error">
            <error type="cancel" code="501">
              <feature-not-implemented
                  xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
              <text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">
                We don&apos;t do things that way here.
              </text>
            </error>
          </message>
        """)

    def testUnknownException(self):
        """Test raising an generic exception in a threaded handler."""

        raised_errors = []

        def message(msg):
            raise ValueError("Did something wrong")

        def catch_error(*args, **kwargs):
            raised_errors.append(True)

        self.stream_start()
        self.xmpp.exception = catch_error
        self.xmpp.add_event_handler('message', message)

        self.recv("""
          <message>
            <body>This is going to cause an error.</body>
          </message>
        """)

        self.send("""
          <message type="error">
            <error type="cancel" code="500">
              <undefined-condition
                  xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
              <text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">
                SleekXMPP got into trouble.
              </text>
            </error>
          </message>
        """)

        self.assertEqual(raised_errors, [True], "Exception was not raised: %s" % raised_errors)

    def testUnknownException(self):
        """Test Sleek continues to respond after an unknown exception."""

        raised_errors = []

        def message(msg):
            raise ValueError("Did something wrong")

        def catch_error(*args, **kwargs):
            raised_errors.append(True)

        self.stream_start()
        self.xmpp.exception = catch_error
        self.xmpp.add_event_handler('message', message)

        self.recv("""
          <message>
            <body>This is going to cause an error.</body>
          </message>
        """)

        self.send("""
          <message type="error">
            <error type="cancel" code="500">
              <undefined-condition
                  xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
              <text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">
                SleekXMPP got into trouble.
              </text>
            </error>
          </message>
        """)

        self.recv("""
          <message>
            <body>This is going to cause an error.</body>
          </message>
        """)

        self.send("""
          <message type="error">
            <error type="cancel" code="500">
              <undefined-condition
                  xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
              <text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">
                SleekXMPP got into trouble.
              </text>
            </error>
          </message>
        """)

        self.assertEqual(raised_errors, [True, True], "Exceptions were not raised: %s" % raised_errors)


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamExceptions)
