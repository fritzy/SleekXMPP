from sleekxmpp.test import *
from sleekxmpp.stanza import Message
from sleekxmpp.xmlstream.stanzabase import ET
from sleekxmpp.xmlstream.tostring import tostring, xml_escape


class TestToString(SleekTest):

    """
    Test the implementation of sleekxmpp.xmlstream.tostring
    """

    def tryTostring(self, original='', expected=None, message='', **kwargs):
        """
        Compare the result of calling tostring against an
        expected result.
        """
        if not expected:
            expected=original
        if isinstance(original, str):
            xml = ET.fromstring(original)
        else:
            xml=original
        result = tostring(xml, **kwargs)
        self.failUnless(result == expected, "%s: %s" % (message, result))

    def testXMLEscape(self):
        """Test escaping XML special characters."""
        original = """<foo bar="baz">'Hi & welcome!'</foo>"""
        escaped = xml_escape(original)
        desired = """&lt;foo bar=&quot;baz&quot;&gt;&apos;Hi"""
        desired += """ &amp; welcome!&apos;&lt;/foo&gt;"""

        self.failUnless(escaped == desired,
            "XML escaping did not work: %s." % escaped)

    def testEmptyElement(self):
        """Test converting an empty element to a string."""
        self.tryTostring(
            original='<bar xmlns="foo" />',
            message="Empty element not serialized correctly")

    def testEmptyElementWrapped(self):
        """Test converting an empty element inside another element."""
        self.tryTostring(
            original='<bar xmlns="foo"><baz /></bar>',
            message="Wrapped empty element not serialized correctly")

    def testEmptyElementWrappedText(self):
        """
        Test converting an empty element wrapped with text
        inside another element.
        """
        self.tryTostring(
            original='<bar xmlns="foo">Some text. <baz /> More text.</bar>',
            message="Text wrapped empty element serialized incorrectly")

    def testMultipleChildren(self):
        """Test converting multiple child elements to a Unicode string."""
        self.tryTostring(
            original='<bar xmlns="foo"><baz><qux /></baz><quux /></bar>',
            message="Multiple child elements not serialized correctly")

    def testXMLNS(self):
        """
        Test using xmlns tostring parameter, which will prevent adding
        an xmlns attribute to the serialized element if the element's
        namespace is the same.
        """
        self.tryTostring(
            original='<bar xmlns="foo" />',
            expected='<bar />',
            message="The xmlns parameter was not used properly.",
            xmlns='foo')

    def testTailContent(self):
        """
        Test that elements of the form <a>foo <b>bar</b> baz</a> only
        include " baz" once.
        """
        self.tryTostring(
            original='<a>foo <b>bar</b> baz</a>',
            message='Element tail content is incorrect.')


    def testStanzaNs(self):
        """
        Test using the stanza_ns tostring parameter, which will prevent
        adding an xmlns attribute to the serialized element if the
        element's namespace is the same.
        """
        self.tryTostring(
            original='<bar xmlns="foo" />',
            expected='<bar />',
            message="The stanza_ns parameter was not used properly.",
            stanza_ns='foo')

    def testStanzaStr(self):
        """
        Test that stanza objects are serialized properly.
        """
        utf8_message = '\xe0\xb2\xa0_\xe0\xb2\xa0'
        if not hasattr(utf8_message, 'decode'):
            # Python 3
            utf8_message = bytes(utf8_message, encoding='utf-8')
        msg = Message()
        msg['body'] = utf8_message.decode('utf-8')
        expected = '<message><body>\xe0\xb2\xa0_\xe0\xb2\xa0</body></message>'
        result = msg.__str__()
        self.failUnless(result == expected,
             "Stanza Unicode handling is incorrect: %s" % result)


suite = unittest.TestLoader().loadTestsFromTestCase(TestToString)
