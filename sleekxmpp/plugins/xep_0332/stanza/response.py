"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of HTTP over XMPP transport
    http://xmpp.org/extensions/xep-0332.html
    Copyright (C) 2015 Riptide IO, sangeeth@riptideio.com
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp import Iq
from sleekxmpp.xmlstream import ElementBase, register_stanza_plugin
from sleekxmpp.plugins.xep_0131.stanza import Headers


class Response(ElementBase):
    pass


register_stanza_plugin(Iq, Response)
register_stanza_plugin(Response, Headers)
