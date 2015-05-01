"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of HTTP over XMPP transport
    http://xmpp.org/extensions/xep-0332.html
    Copyright (C) 2015 Riptide IO, sangeeth@riptideio.com
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ElementBase


class HTTPRequest(ElementBase):

    """
    All HTTP communication is done using the `Request`/`Response` paradigm.
    Each HTTP Request is made sending an `iq` stanza containing a `req`
    element to the server. Each `iq` stanza sent is of type `set`.

    Examples:
    <iq type='set' from='a@b.com/browser' to='x@y.com' id='1'>
        <req xmlns='urn:xmpp:http'
             method='GET'
             resource='/api/users'
             version='1.1'>
            <headers xmlns='http://jabber.org/protocol/shim'>
                <header name='Host'>b.com</header>
            </headers>
        </req>
    </iq>

    <iq type='set' from='a@b.com/browser' to='x@y.com' id='2'>
        <req xmlns='urn:xmpp:http'
             method='PUT'
             resource='/api/users'
             version='1.1'>
            <headers xmlns='http://jabber.org/protocol/shim'>
                <header name='Host'>b.com</header>
                <header name='Content-Type'>text/html</header>
                <header name='Content-Length'>...</header>
            </headers>
            <data>
                <text>...</text>
            </data>
        </req>
    </iq>
    """

    name = 'request'
    namespace = 'urn:xmpp:http'
    interfaces = set(['method', 'resource', 'version'])
    plugin_attrib = 'http-req'

    def get_method(self):
        return self._get_attr('method', None)

    def set_method(self, method):
        self._set_attr('method', method)

    def get_resource(self):
        return self._get_attr('resource', None)

    def set_resource(self, resource):
        self._set_attr('resource', resource)

    def get_version(self):
        return self._get_attr('version', None)

    def set_version(self, version='1.1'):
        self._set_attr('version', version)
