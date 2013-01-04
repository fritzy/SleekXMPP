"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.plugins.base import register_plugin

from sleekxmpp.plugins.xep_0048.stanza import Bookmarks, Conference, URL
from sleekxmpp.plugins.xep_0048.bookmarks import XEP_0048


register_plugin(XEP_0048)
