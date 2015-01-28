"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of HTTP over XMPP transport
    http://xmpp.org/extensions/xep-0332.html
    Copyright (C) 2015 Riptide IO, sangeeth@riptideio.com
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp import Iq

from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath

from sleekxmpp.plugins.base import BasePlugin

from sleekxmpp.plugins.xep_0332.stanza import NAMESPACE
from sleekxmpp.plugins.xep_0332.stanza.request import Request
from sleekxmpp.plugins.xep_0332.stanza.response import Response

from sleekxmpp.plugins.xep_0131.stanza import Headers


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

        self.xmpp.register_handler(Callback(
            'HTTP Request', StanzaPath('iq/req'), self._handle_request
        ))
        self.xmpp.register_handler(Callback(
            'HTTP Response', StanzaPath('iq/resp'), self._handle_response
        ))

        register_stanza_plugin(Iq, Request)
        register_stanza_plugin(Iq, Response)
        register_stanza_plugin(Request, Headers)
        register_stanza_plugin(Response, Headers)

    def plugin_end(self):
        log.debug("XEP_0332:: plugin_end()")
        self.xmpp.remove_handler('HTTP Request')
        self.xmpp.remove_handler('HTTP Response')
        self.xmpp['xep_0030'].del_feature(NAMESPACE)

    def session_bind(self, jid):
        log.debug("XEP_0332:: session_bind()")
        self.xmpp['xep_0030'].add_feature(NAMESPACE)

    def _handle_request(self):
        log.debug("XEP_0332:: _handle_request()")

    def _handle_response(self):
        log.debug("XEP_0332:: _handle_response()")

    def send_request(self, method=None, resource=None, headers=None, data=None, **kwargs):
        log.debug("XEP_0332:: send_request()")

    def send_response(self, status_code=None, headers=None, data=None, **kwargs):
        log.debug("XEP_0332:: send_response()")

