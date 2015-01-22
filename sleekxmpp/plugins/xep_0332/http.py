"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of HTTP over XMPP transport
    http://xmpp.org/extensions/xep-0332.html
    Copyright (C) 2015 Riptide IO, sangeeth@riptideio.com
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.plugins.base import BasePlugin


log = logging.getLogger(__name__)


class XEP_0332(BasePlugin):
    """
    XEP-0332: HTTP over XMPP transport
    """

    name = 'xep_0332'
    description = 'XEP-0332: HTTP over XMPP transport'
    dependencies = set(['xep_0030', 'xep_0047', 'xep_0131'])    #: xep 1, 137 and 166 are missing
    default_config = {}

    def plugin_init(self):
        log.debug("XEP_0332:: plugin_init()")

    def plugin_end(self):
        log.debug("XEP_0332:: plugin_end()")

    def session_bind(self, jid):
        log.debug("XEP_0332:: session_bind()")

