"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""


class BaseHandler(object):

    """
    Base class for stream handlers. Stream handlers are matched with
    incoming stanzas so that the stanza may be processed in some way.
    Stanzas may be matched with multiple handlers.

    Handler execution may take place in two phases. The first is during
    the stream processing itself. The second is after stream processing
    and during SleekXMPP's main event loop. The prerun method is used
    for execution during stream processing, and the run method is used
    during the main event loop.

    Attributes:
        name   -- The name of the handler.
        stream -- The stream this handler is assigned to.

    Methods:
        match        -- Compare a stanza with the handler's matcher.
        prerun       -- Handler execution during stream processing.
        run          -- Handler execution during the main event loop.
        check_delete -- Indicate if the handler may be removed from use.
    """

    def __init__(self, name, matcher, stream=None):
        """
        Create a new stream handler.

        Arguments:
            name    -- The name of the handler.
            matcher -- A matcher object from xmlstream.matcher that will be
                       used to determine if a stanza should be accepted by
                       this handler.
            stream  -- The XMLStream instance the handler should monitor.
        """
        self.checkDelete = self.check_delete

        self.name = name
        self.stream = stream
        self._destroy = False
        self._payload = None
        self._matcher = matcher
        if stream is not None:
            stream.registerHandler(self)

    def match(self, xml):
        """
        Compare a stanza or XML object with the handler's matcher.

        Arguments
            xml -- An XML or stanza object.
        """
        return self._matcher.match(xml)

    def prerun(self, payload):
        """
        Prepare the handler for execution while the XML stream is being
        processed.

        Arguments:
            payload -- A stanza object.
        """
        self._payload = payload

    def run(self, payload):
        """
        Execute the handler after XML stream processing and during the
        main event loop.

        Arguments:
            payload -- A stanza object.
        """
        self._payload = payload

    def check_delete(self):
        """
        Check if the handler should be removed from the list of stream
        handlers.
        """
        return self._destroy
