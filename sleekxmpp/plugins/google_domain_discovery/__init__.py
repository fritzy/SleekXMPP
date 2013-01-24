"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.plugins.base import register_plugin

from sleekxmpp.plugins.google_domain_discovery import stanza
from sleekxmpp.plugins.google_domain_discovery.auth import GoogleDomainDiscovery


register_plugin(GoogleDomainDiscovery)
