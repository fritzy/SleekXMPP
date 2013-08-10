"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging
if hasattr(logging, 'NullHandler'):
    NullHandler = logging.NullHandler
else:
    class NullHandler(logging.Handler):
        def handle(self, record):
            pass
logging.getLogger(__name__).addHandler(NullHandler())
del NullHandler


from sleekxmpp.stanza import Message, Presence, Iq
from sleekxmpp.jid import JID, InvalidJID
from sleekxmpp.xmlstream.stanzabase import ET, ElementBase, register_stanza_plugin
from sleekxmpp.xmlstream.handler import *
from sleekxmpp.xmlstream import XMLStream, RestartStream
from sleekxmpp.xmlstream.matcher import *
from sleekxmpp.basexmpp import BaseXMPP
from sleekxmpp.clientxmpp import ClientXMPP
from sleekxmpp.componentxmpp import ComponentXMPP

from sleekxmpp.version import __version__, __version_info__
