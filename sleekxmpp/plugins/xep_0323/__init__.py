"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Sustainable Innovation, Joachim.lindborg@sust.se, bjorn.westrom@consoden.se
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.plugins.base import register_plugin

from sleekxmpp.plugins.xep_0323.sensordata import XEP_0323
from sleekxmpp.plugins.xep_0323 import stanza

register_plugin(XEP_0323)

xep_0323=XEP_0323
