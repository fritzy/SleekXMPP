"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging
try:
    import queue
except ImportError:
    import Queue as queue

from sleekxmpp.xmlstream import StanzaBase, RESPONSE_TIMEOUT
from sleekxmpp.xmlstream.handler.base import BaseHandler


log = logging.getLogger(__name__)


class Waiter(BaseHandler):

    """
    The Waiter handler allows an event handler to block
    until a particular stanza has been received. The handler
    will either be given the matched stanza, or False if the
    waiter has timed out.

    Methods:
        check_delete -- Overrides BaseHandler.check_delete
        prerun       -- Overrides BaseHandler.prerun
        run          -- Overrides BaseHandler.run
        wait         -- Wait for a stanza to arrive and return it to
                        an event handler.
    """

    def __init__(self, name, matcher, stream=None):
        """
        Create a new Waiter.

        Arguments:
            name    -- The name of the waiter.
            matcher -- A matcher object to detect the desired stanza.
            stream  -- Optional XMLStream instance to monitor.
        """
        BaseHandler.__init__(self, name, matcher, stream=stream)
        self._payload = queue.Queue()

    def prerun(self, payload):
        """
        Store the matched stanza.

        Overrides BaseHandler.prerun

        Arguments:
            payload -- The matched stanza object.
        """
        self._payload.put(payload)

    def run(self, payload):
        """
        Do not process this handler during the main event loop.

        Overrides BaseHandler.run

        Arguments:
            payload -- The matched stanza object.
        """
        pass

    def wait(self, timeout=RESPONSE_TIMEOUT):
        """
        Block an event handler while waiting for a stanza to arrive.

        Be aware that this will impact performance if called from a
        non-threaded event handler.

        Will return either the received stanza, or False if the waiter
        timed out.

        Arguments:
            timeout -- The number of seconds to wait for the stanza to
                       arrive. Defaults to the global default timeout
                       value sleekxmpp.xmlstream.RESPONSE_TIMEOUT.
        """
        try:
            stanza = self._payload.get(True, timeout)
        except queue.Empty:
            stanza = False
            log.warning("Timed out waiting for %s" % self.name)
        self.stream.removeHandler(self.name)
        return stanza

    def check_delete(self):
        """
        Always remove waiters after use.

        Overrides BaseHandler.check_delete
        """
        return True
