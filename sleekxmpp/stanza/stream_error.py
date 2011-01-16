"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza.error import Error
from sleekxmpp.xmlstream import ElementBase, ET, register_stanza_plugin


class StreamError(Error):

    """
    XMPP stanzas of type 'error' should include an <error> stanza that
    describes the nature of the error and how it should be handled.

    Use the 'XEP-0086: Error Condition Mappings' plugin to include error
    codes used in older XMPP versions.

    The stream:error stanza is used to provide more information for
    error that occur with the underlying XML stream itself, and not
    a particular stanza.

    Note: The StreamError stanza is the same as the normal Error stanza,
          but with a different namespace.

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
        setup         -- Overrides ElementBase.setup.
        get_condition -- Retrieve the name of the condition element.
        set_condition -- Add a condition element.
        del_condition -- Remove the condition element.
        get_text      -- Retrieve the contents of the <text> element.
        set_text      -- Set the contents of the <text> element.
        del_text      -- Remove the <text> element.
    """

    namespace = 'http://etherx.jabber.org/streams'
