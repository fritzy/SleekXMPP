"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import Message
from sleekxmpp.xmlstream.stanzabase import registerStanzaPlugin
from sleekxmpp.xmlstream.stanzabase import ElementBase, ET


class HTMLIM(ElementBase):

    """
    XEP-0071: XHTML-IM defines a method for embedding XHTML content
    within a <message> stanza so that lightweight markup can be used
    to format the message contents and to create links.

    Only a subset of XHTML is recommended for use with XHTML-IM.
    See the full spec at 'http://xmpp.org/extensions/xep-0071.html'
    for more information.

    Example stanza:
        <message to="user@example.com">
          <body>Non-html message content.</body>
          <html xmlns="http://jabber.org/protocol/xhtml-im">
            <body xmlns="http://www.w3.org/1999/xhtml">
              <p><b>HTML!</b></p>
            </body>
          </html>
        </message>

    Stanza Interface:
        body -- The contents of the HTML body tag.

    Methods:
        getBody -- Return the HTML body contents.
        setBody -- Set the HTML body contents.
        delBody -- Remove the HTML body contents.
    """

    namespace = 'http://jabber.org/protocol/xhtml-im'
    name = 'html'
    interfaces = set(('body',))
    plugin_attrib = name

    def setBody(self, html):
        """
        Set the contents of the HTML body.

        Arguments:
            html -- Either a string or XML object. If the top level
                    element is not <body> with a namespace of
                    'http://www.w3.org/1999/xhtml', it will be wrapped.
        """
        if isinstance(html, str):
            html = ET.XML(html)
        if html.tag != '{http://www.w3.org/1999/xhtml}body':
            body = ET.Element('{http://www.w3.org/1999/xhtml}body')
            body.append(html)
            self.xml.append(body)
        else:
            self.xml.append(html)

    def getBody(self):
        """Return the contents of the HTML body."""
        html = self.xml.find('{http://www.w3.org/1999/xhtml}body')
        if html is None:
            return ''
        return html

    def delBody(self):
        """Remove the HTML body contents."""
        if self.parent is not None:
            self.parent().xml.remove(self.xml)


registerStanzaPlugin(Message, HTMLIM)
