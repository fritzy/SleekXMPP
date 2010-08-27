"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream.handler.base import BaseHandler


class Callback(BaseHandler):

    """
    The Callback handler will execute a callback function with
    matched stanzas.

    The handler may execute the callback either during stream
    processing or during the main event loop.

    Callback functions are all executed in the same thread, so be
    aware if you are executing functions that will block for extended
    periods of time. Typically, you should signal your own events using the
    SleekXMPP object's event() method to pass the stanza off to a threaded
    event handler for further processing.

    Methods:
        prerun -- Overrides BaseHandler.prerun
        run    -- Overrides BaseHandler.run
    """

    def __init__(self, name, matcher, pointer, thread=False,
                 once=False, instream=False, stream=None):
        """
        Create a new callback handler.

        Arguments:
            name     -- The name of the handler.
            matcher  -- A matcher object for matching stanza objects.
            pointer  -- The function to execute during callback.
            thread   -- DEPRECATED. Remains only for backwards compatibility.
            once     -- Indicates if the handler should be used only
                        once. Defaults to False.
            instream -- Indicates if the callback should be executed
                        during stream processing instead of in the
                        main event loop.
            stream   -- The XMLStream instance this handler should monitor.
        """
        BaseHandler.__init__(self, name, matcher, stream)
        self._pointer = pointer
        self._once = once
        self._instream = instream

    def prerun(self, payload):
        """
        Execute the callback during stream processing, if
        the callback was created with instream=True.

        Overrides BaseHandler.prerun

        Arguments:
            payload -- The matched stanza object.
        """
        BaseHandler.prerun(self, payload)
        if self._instream:
            self.run(payload, True)

    def run(self, payload, instream=False):
        """
        Execute the callback function with the matched stanza payload.

        Overrides BaseHandler.run

        Arguments:
            payload  -- The matched stanza object.
            instream -- Force the handler to execute during
                        stream processing. Used only by prerun.
                        Defaults to False.
        """
        if not self._instream or instream:
            BaseHandler.run(self, payload)
            self._pointer(payload)
            if self._once:
                self._destroy = True
