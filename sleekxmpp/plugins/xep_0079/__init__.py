"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.plugins.base import register_plugin

from sleekxmpp.plugins.xep_0079.stanza import (
        AMP, Rule, InvalidRules, UnsupportedConditions,
        UnsupportedActions, FailedRules, FailedRule,
        AMPFeature)
from sleekxmpp.plugins.xep_0079.amp import XEP_0079


register_plugin(XEP_0079)
