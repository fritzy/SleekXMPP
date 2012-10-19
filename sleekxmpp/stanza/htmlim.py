"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import Message
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins.xep_0071 import XHTML_IM as HTMLIM


register_stanza_plugin(Message, HTMLIM)


# To comply with PEP8, method names now use underscores.
# Deprecated method names are re-mapped for backwards compatibility.
HTMLIM.setBody = HTMLIM.set_body
HTMLIM.getBody = HTMLIM.get_body
HTMLIM.delBody = HTMLIM.del_body
