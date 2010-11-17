"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging
import traceback
import sys

from sleekxmpp.exceptions import XMPPError
from sleekxmpp.stanza import Error
from sleekxmpp.xmlstream import ET, StanzaBase, register_stanza_plugin


log = logging.getLogger(__name__)


class RootStanza(StanzaBase):

    """
    A top-level XMPP stanza in an XMLStream.

    The RootStanza class provides a more XMPP specific exception
    handler than provided by the generic StanzaBase class.

    Methods:
        exception -- Overrides StanzaBase.exception
    """

    def exception(self, e):
        """
        Create and send an error reply.

        Typically called when an event handler raises an exception.
        The error's type and text content are based on the exception
        object's type and content.

        Overrides StanzaBase.exception.

        Arguments:
            e -- Exception object
        """
        self.reply()
        if isinstance(e, XMPPError):
            # We raised this deliberately
            self['error']['condition'] = e.condition
            self['error']['text'] = e.text
            if e.extension is not None:
                # Extended error tag
                extxml = ET.Element("{%s}%s" % (e.extension_ns, e.extension),
                                    e.extension_args)
                self['error'].append(extxml)
                self['error']['type'] = e.etype
        else:
            # We probably didn't raise this on purpose, so send a traceback
            self['error']['condition'] = 'undefined-condition'
            if sys.version_info < (3, 0):
                self['error']['text'] = "SleekXMPP got into trouble."
            else:
                self['error']['text'] = traceback.format_tb(e.__traceback__)
                log.exception('Error handling {%s}%s stanza' %
                                  (self.namespace, self.name))
        self.send()


register_stanza_plugin(RootStanza, Error)
