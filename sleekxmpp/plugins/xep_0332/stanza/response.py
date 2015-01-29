"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of HTTP over XMPP transport
    http://xmpp.org/extensions/xep-0332.html
    Copyright (C) 2015 Riptide IO, sangeeth@riptideio.com
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ElementBase


class Response(ElementBase):

    """
    When the HTTP Server responds, it does so by sending an `iq` stanza
    response (type=`result`) back to the client containing the `resp` element.
    Since response are asynchronous, and since multiple requests may be active
    at the same time, responses may be returned in a different order than the
    in which the original requests were made.

    Examples:
    <iq type='result' from='httpserver@clayster.com' to='httpclient@clayster.com/browser' id='2'>
        <resp xmlns='urn:xmpp:http' version='1.1' statusCode='200' statusMessage='OK'>
            <headers xmlns='http://jabber.org/protocol/shim'>
                <header name='Date'>Fri, 03 May 2013 16:39:54GMT-4</header>
                <header name='Server'>Clayster</header>
                <header name='Content-Type'>text/turtle</header>
                <header name='Content-Length'>...</header>
                <header name='Connection'>Close</header>
            </headers>
            <data>
                <text>
                    ...
                </text>
            </data>
        </resp>
    </iq>
    """

    name = 'response'
    namespace = 'urn:xmpp:http'
    interfaces = set(['code', 'version'])
    plugin_attrib = 'resp'

    def get_code(self):
        print "Response:: get_code()"

    def set_code(self, code):
        print "Response:: set_code()"
        self._set_attr('statusCode', str(code))
        self._set_attr('statusMessage', str(code))

    def set_version(self, version='1.1'):
        print "Response:: set_version()"
        self._set_attr('version', version)
