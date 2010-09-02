"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream.matcher.base import MatcherBase


class MatcherId(MatcherBase):

    """
    The ID matcher selects stanzas that have the same stanza 'id'
    interface value as the desired ID.

    Methods:
        match -- Overrides MatcherBase.match.
    """

    def match(self, xml):
        """
        Compare the given stanza's 'id' attribute to the stored
        id value.

        Overrides MatcherBase.match.

        Arguments:
            xml -- The stanza to compare against.
        """
        return xml['id'] == self._criteria
