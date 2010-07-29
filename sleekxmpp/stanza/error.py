"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream.stanzabase import registerStanzaPlugin
from sleekxmpp.xmlstream.stanzabase import ElementBase, ET


class Error(ElementBase):

    """
    XMPP stanzas of type 'error' should include an <error> stanza that
    describes the nature of the error and how it should be handled.

    Use the 'XEP-0086: Error Condition Mappings' plugin to include error
    codes used in older XMPP versions.

    Example error stanza:
        <error type="cancel" code="404">
          <item-not-found xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
          <text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">
            The item was not found.
          </text>
        </error>

    Stanza Interface:
        code      -- The error code used in older XMPP versions.
        condition -- The name of the condition element.
        text      -- Human readable description of the error.
        type      -- Error type indicating how the error should be handled.

    Attributes:
        conditions   -- The set of allowable error condition elements.
        condition_ns -- The namespace for the condition element.
        types        -- A set of values indicating how the error
                        should be treated.

    Methods:
        setup        -- Overrides ElementBase.setup.
        getCondition -- Retrieve the name of the condition element.
        setCondition -- Add a condition element.
        delCondition -- Remove the condition element.
        getText      -- Retrieve the contents of the <text> element.
        setText      -- Set the contents of the <text> element.
        delText      -- Remove the <text> element.
    """

    namespace = 'jabber:client'
    name = 'error'
    plugin_attrib = 'error'
    interfaces = set(('code', 'condition', 'text', 'type'))
    sub_interfaces = set(('text',))
    conditions = set(('bad-request', 'conflict', 'feature-not-implemented',
                      'forbidden', 'gone', 'internal-server-error',
                      'item-not-found', 'jid-malformed', 'not-acceptable',
                      'not-allowed', 'not-authorized', 'payment-required',
                      'recipient-unavailable', 'redirect',
                      'registration-required', 'remote-server-not-found',
                      'remote-server-timeout', 'resource-constraint',
                      'service-unavailable', 'subscription-required',
                      'undefined-condition', 'unexpected-request'))
    condition_ns = 'urn:ietf:params:xml:ns:xmpp-stanzas'
    types = set(('cancel', 'continue', 'modify', 'auth', 'wait'))

    def setup(self, xml=None):
        """
        Populate the stanza object using an optional XML object.

        Overrides ElementBase.setup.

        Sets a default error type and condition, and changes the
        parent stanza's type to 'error'.

        Arguments:
            xml -- Use an existing XML object for the stanza's values.
        """
        if ElementBase.setup(self, xml):
            #If we had to generate XML then set default values.
            self['type'] = 'cancel'
            self['condition'] = 'feature-not-implemented'
        if self.parent is not None:
            self.parent()['type'] = 'error'

    def getCondition(self):
        """Return the condition element's name."""
        for child in self.xml.getchildren():
            if "{%s}" % self.condition_ns in child.tag:
                return child.tag.split('}', 1)[-1]
        return ''

    def setCondition(self, value):
        """
        Set the tag name of the condition element.

        Arguments:
           value -- The tag name of the condition element.
        """
        if value in self.conditions:
            del self['condition']
            self.xml.append(ET.Element("{%s}%s" % (self.condition_ns, value)))
        return self

    def delCondition(self):
        """Remove the condition element."""
        for child in self.xml.getchildren():
            if "{%s}" % self.condition_ns in child.tag:
                self.xml.remove(child)
        return self

    def getText(self):
        """Retrieve the contents of the <text> element."""
        return self._getSubText('{%s}text' % self.condition_ns)

    def setText(self, value):
        """
        Set the contents of the <text> element.

        Arguments:
            value -- The new contents for the <text> element.
        """
        self._setSubText('{%s}text' % self.condition_ns, text=value)
        return self

    def delText(self):
        """Remove the <text> element."""
        self._delSub('{%s}text' % self.condition_ns)
        return self
