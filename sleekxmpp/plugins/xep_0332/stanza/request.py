"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of HTTP over XMPP transport
    http://xmpp.org/extensions/xep-0332.html
    Copyright (C) 2015 Riptide IO, sangeeth@riptideio.com
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ElementBase
from sleekxmpp.plugins.xep_0332.stanza import NAMESPACE


class Request(ElementBase):

    """
    All HTTP communication is done using the `Request`/`Response` paradigm.
    Each HTTP Request is made sending an `iq` stanza containing a `req` element
    to the server. Each `iq` stanza sent is of type `set`.

    Examples:
    <iq type='set' from='a@b.com/browser' to='x@y.com' id='1'>
        <req xmlns='urn:xmpp:http' method='GET' resource='/api/user' version='1.1'>
            <headers xmlns='http://jabber.org/protocol/shim'>
                <header name='Host'>b.com</header>
            </headers>
        </req>
    </iq>

    <iq type='set' from='a@b.com/browser' to='x@y.com' id='2'>
        <req xmlns='urn:xmpp:http' method='PUT' resource='/api/users' version='1.1'>
            <headers xmlns='http://jabber.org/protocol/shim'>
                <header name='Host'>b.com</header>
                <header name='Content-Type'>text/html</header>
                <header name='Content-Length'>...</header>
            </headers>
            <data>
                <text>&lt;html&gt;&lt;header/&gt;&lt;body&gt;&lt;p&gt;Beautiful home page.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</text>
            </data>
        </req>
    </iq>
    """

    name = 'request'
    namespace = NAMESPACE
    interfaces = set(('method', 'resource', 'version'))
    plugin_attrib = 'req'

