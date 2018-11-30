# -*- coding: utf-8 -*-
"""
    sleekxmpp.xmlstream.matcher.xpath
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Part of SleekXMPP: The Sleek XMPP Library

    :copyright: (c) 2011 Nathanael C. Fritz
    :license: MIT, see LICENSE for more details
"""

from sleekxmpp.xmlstream.stanzabase import ET, fix_ns
from sleekxmpp.xmlstream.matcher.base import MatcherBase


class MatchXPath(MatcherBase):

    """
    The XPath matcher selects stanzas whose XML contents matches a given
    XPath expression.

    If the value of :data:`IGNORE_NS` is set to ``True``, then XPath
    expressions will be matched without using namespaces.
    """

    def __init__(self, criteria):
        self._criteria = fix_ns(criteria)

    def match(self, xml):
        """
        Compare a stanza's XML contents to an XPath expression.

        If the value of :data:`IGNORE_NS` is set to ``True``, then XPath
        expressions will be matched without using namespaces.

        :param xml: The :class:`~sleekxmpp.xmlstream.stanzabase.ElementBase`
                    stanza to compare against.
        """
        if hasattr(xml, 'xml'):
            xml = xml.xml
        x = ET.Element('x')
        x.append(xml)

        return x.find(self._criteria) is not None
