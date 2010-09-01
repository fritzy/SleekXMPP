"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream.stanzabase import ET
from sleekxmpp.xmlstream.matcher.base import MatcherBase


# Flag indicating if the builtin XPath matcher should be used, which
# uses namespaces, or a custom matcher that ignores namespaces.
# Changing this will affect ALL XPath matchers.
IGNORE_NS = False


class MatchXPath(MatcherBase):

    """
    The XPath matcher selects stanzas whose XML contents matches a given
    XPath expression.

    Note that using this matcher may not produce expected behavior when using
    attribute selectors. For Python 2.6 and 3.1, the ElementTree find method
    does not support the use of attribute selectors. If you need to support
    Python 2.6 or 3.1, it might be more useful to use a StanzaPath matcher.

    If the value of IGNORE_NS is set to true, then XPath expressions will
    be matched without using namespaces.

    Methods:
        match -- Overrides MatcherBase.match.
    """

    def match(self, xml):
        """
        Compare a stanza's XML contents to an XPath expression.

        If the value of IGNORE_NS is set to true, then XPath expressions
        will be matched without using namespaces.

        Note that in Python 2.6 and 3.1 the ElementTree find method does
        not support attribute selectors in the XPath expression.

        Arguments:
            xml -- The stanza object to compare against.
        """
        if hasattr(xml, 'xml'):
            xml = xml.xml
        x = ET.Element('x')
        x.append(xml)

        if not IGNORE_NS:
            # Use builtin, namespace respecting, XPath matcher.
            if x.find(self._criteria) is not None:
                return True
            return False
        else:
            # Remove namespaces from the XPath expression.
            criteria = []
            for ns_block in self._criteria.split('{'):
                criteria.extend(ns_block.split('}')[-1].split('/'))

            # Walk the XPath expression.
            xml = x
            for tag in criteria:
                if not tag:
                    # Skip empty tag name artifacts from the cleanup phase.
                    continue

                children = [c.tag.split('}')[-1] for c in xml.getchildren()]
                try:
                    index = children.index(tag)
                except ValueError:
                    return False
                xml = xml.getchildren()[index]
            return True
