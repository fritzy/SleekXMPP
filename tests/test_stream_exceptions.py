import sys
import sleekxmpp
from sleekxmpp.exceptions import XMPPError
from sleekxmpp.test import *


class TestStreamExceptions(SleekTest):
    """
    Test handling roster updates.
    """

    def tearDown(self):
        self.stream_close()

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
            <error type="cancel">
              <feature-not-implemented
                  xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
              <text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">
                We don&apos;t do things that way here.
              </text>
              <foo xmlns="foo:error" test="true" />
            </error>
          </message>
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
            <error type="cancel">
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

        def message(msg):
            raise ValueError("Did something wrong")

        self.stream_start()
        self.xmpp.add_event_handler('message', message)

        self.recv("""
          <message>
            <body>This is going to cause an error.</body>
          </message>
        """)

        if sys.version_info < (3, 0):
            self.send("""
              <message type="error">
                <error type="cancel">
                  <undefined-condition
                      xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
                  <text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">
                    SleekXMPP got into trouble.
                  </text>
                </error>
              </message>
            """)
        else:
            # Unfortunately, tracebacks do not make for very portable tests.
            pass


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamExceptions)
