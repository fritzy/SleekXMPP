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
from sleekxmpp.plugins.xep_0332.stanza import Request, Response, Data
from sleekxmpp.plugins.xep_0131.stanza import Headers


log = logging.getLogger(__name__)


class XEP_0332(BasePlugin):
    """
    XEP-0332: HTTP over XMPP transport
    """

    name = 'xep_0332'
    description = 'XEP-0332: HTTP over XMPP transport'

    #: xep_0047 not included.
    #: xep_0001, 0137 and 0166 are missing
    dependencies = set(['xep_0030', 'xep_0131'])

    #: TODO: Do we really need to mention the supported_headers?!
    default_config = {
        'supported_headers': set([
            'Content-Length', 'Transfer-Encoding', 'DateTime',
            'Accept-Charset', 'Location', 'Content-ID', 'Description',
            'Content-Language', 'Content-Transfer-Encoding', 'Timestamp',
            'Expires', 'User-Agent', 'Host', 'Proxy-Authorization', 'Date',
            'WWW-Authenticate', 'Accept-Encoding', 'Server', 'Error-Info',
            'Identifier', 'Content-Location', 'Content-Encoding', 'Distribute',
            'Accept', 'Proxy-Authenticate', 'ETag', 'Expect', 'Content-Type'
        ])
    }

    def plugin_init(self):
        log.debug("XEP_0332:: plugin_init()")

        self.xmpp.register_handler(Callback(
            'HTTP Request', StanzaPath('iq/req'), self._handle_request
        ))
        self.xmpp.register_handler(Callback(
            'HTTP Response', StanzaPath('iq/resp'), self._handle_response
        ))

        register_stanza_plugin(Iq, Request, iterable=True)
        register_stanza_plugin(Iq, Response, iterable=True)
        register_stanza_plugin(Request, Headers, iterable=True)
        register_stanza_plugin(Request, Data, iterable=True)
        register_stanza_plugin(Response, Headers, iterable=True)
        register_stanza_plugin(Response, Data, iterable=True)

        # TODO: Should we register any api's here? self.api.register()

    def plugin_end(self):
        log.debug("XEP_0332:: plugin_end()")
        self.xmpp.remove_handler('HTTP Request')
        self.xmpp.remove_handler('HTTP Response')
        self.xmpp['xep_0030'].del_feature('urn:xmpp:http')
        for header in self.supported_headers:
            self.xmpp['xep_0030'].del_feature(
                feature='%s#%s' % (Headers.namespace, header)
            )

    def session_bind(self, jid):
        log.debug("XEP_0332:: session_bind()")
        self.xmpp['xep_0030'].add_feature('urn:xmpp:http')
        for header in self.supported_headers:
            self.xmpp['xep_0030'].add_feature(
                '%s#%s' % (Headers.namespace, header)
            )
            # TODO: Do we need to add the supported headers to xep_0131?
            # self.xmpp['xep_0131'].supported_headers.add(header)

    def _handle_request(self, iq):
        log.debug("XEP_0332:: _handle_request()")
        print iq

    def _handle_response(self, iq):
        log.debug("XEP_0332:: _handle_response()")
        print iq

    def send_request(self, to=None, method=None, resource=None, headers=None,
                     data=None, **kwargs):
        log.debug("XEP_0332:: send_request()")
        iq = self.xmpp.Iq()
        iq['from'] = self.xmpp.boundjid
        iq['to'] = to
        iq['type'] = 'set'
        iq['req']['headers'] = headers
        iq['req']['method'] = method
        iq['req']['resource'] = resource
        iq['req']['version'] = '1.1'        # TODO: set this implicitly
        iq['req']['data'] = data
        print iq
        # return iq.send(timeout=kwargs.get('timeout', None),
        #                block=kwargs.get('block', True),
        #                callback=kwargs.get('callback', None),
        #                timeout_callback=kwargs.get('timeout_callback', None))

    def send_response(self, to=None, code=None, headers=None, data=None,
                      **kwargs):
        log.debug("XEP_0332:: send_response()")
        iq = self.xmpp.Iq()
        iq['from'] = self.xmpp.boundjid
        iq['to'] = to
        iq['type'] = 'result'
        iq['resp']['headers'] = headers
        iq['resp']['code'] = code
        iq['resp']['version'] = '1.1'       # TODO: set this implicitly
        iq['resp']['data'] = data
        print iq
        # return iq.send(timeout=kwargs.get('timeout', None),
        # block=kwargs.get('block', True),
        #                callback=kwargs.get('callback', None),
        #                timeout_callback=kwargs.get('timeout_callback', None))

