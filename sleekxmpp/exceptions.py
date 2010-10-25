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

    def __init__(self, condition='undefined-condition', text=None, etype=None,
                 extension=None, extension_ns=None, extension_args=None):
        """
        Create a new XMPPError exception.

        Extension information can be included to add additional XML elements
        to the generated error stanza.

        Arguments:
            condition      -- The XMPP defined error condition.
            text           -- Human readable text describing the error.
            etype          -- The XMPP error type, such as cancel or modify.
            extension      -- Tag name of the extension's XML content.
            extension_ns   -- XML namespace of the extensions' XML content.
            extension_args -- Content and attributes for the extension
                              element. Same as the additional arguments to
                              the ET.Element constructor.
        """
        if extension_args is None:
            extension_args = {}

        self.condition = condition
        self.text = text
        self.etype = etype
        self.extension = extension
        self.extension_ns = extension_ns
        self.extension_args = extension_args
