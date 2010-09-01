"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream.matcher.base import MatcherBase


class StanzaPath(MatcherBase):

    """
    The StanzaPath matcher selects stanzas that match a given "stanza path",
    which is similar to a normal XPath except that it uses the interfaces and
    plugins of the stanza instead of the actual, underlying XML.

    In most cases, the stanza path and XPath should be identical, but be
    aware that differences may occur.

    Methods:
        match -- Overrides MatcherBase.match.
    """

    def match(self, stanza):
        """
        Compare a stanza against a "stanza path". A stanza path is similar to
        an XPath expression, but uses the stanza's interfaces and plugins
        instead of the underlying XML. For most cases, the stanza path and
        XPath should be identical, but be aware that differences may occur.

        Overrides MatcherBase.match.

        Arguments:
            stanza -- The stanza object to compare against.
        """
        return stanza.match(self._criteria)
