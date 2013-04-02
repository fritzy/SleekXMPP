"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.plugins.base import register_plugin

from sleekxmpp.plugins.xep_0004.stanza import Form
from sleekxmpp.plugins.xep_0004.stanza import FormField, FieldOption
from sleekxmpp.plugins.xep_0004.dataforms import XEP_0004


register_plugin(XEP_0004)
