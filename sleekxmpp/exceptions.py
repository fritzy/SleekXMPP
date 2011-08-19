"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""


class XMPPError(Exception):

    """
    A generic exception that may be raised while processing an XMPP stanza
    to indicate that an error response stanza should be sent.

    The exception method for stanza objects extending RootStanza will create
    an error stanza and initialize any additional substanzas using the
    extension information included in the exception.

    Meant for use in SleekXMPP plugins and applications using SleekXMPP.
    """

    def __init__(self, condition='undefined-condition', text=None,
                etype='cancel', extension=None, extension_ns=None,
                extension_args=None, clear=True):
        """
        Create a new XMPPError exception.

        Extension information can be included to add additional XML elements
        to the generated error stanza.

        Arguments:
            condition      -- The XMPP defined error condition.
                              Defaults to 'undefined-condition'.
            text           -- Human readable text describing the error.
            etype          -- The XMPP error type, such as cancel or modify.
                              Defaults to 'cancel'.
            extension      -- Tag name of the extension's XML content.
            extension_ns   -- XML namespace of the extensions' XML content.
            extension_args -- Content and attributes for the extension
                              element. Same as the additional arguments to
                              the ET.Element constructor.
            clear          -- Indicates if the stanza's contents should be
                              removed before replying with an error.
                              Defaults to True.
        """
        if extension_args is None:
            extension_args = {}

        self.condition = condition
        self.text = text
        self.etype = etype
        self.clear = clear
        self.extension = extension
        self.extension_ns = extension_ns
        self.extension_args = extension_args


class IqTimeout(XMPPError):

    """
    An exception which indicates that an IQ request response has not been
    received within the alloted time window.
    """

    def __init__(self, iq):
        super(IqTimeout, self).__init__(
                condition='remote-server-timeout',
                etype='cancel')

        self.iq = iq

class IqError(XMPPError):

    """
    An exception raised when an Iq stanza of type 'error' is received
    after making a blocking send call.
    """

    def __init__(self, iq):
        super(IqError, self).__init__(
                condition=iq['error']['condition'],
                text=iq['error']['text'],
                etype=iq['error']['type'])

        self.iq = iq
