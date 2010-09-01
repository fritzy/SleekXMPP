"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""


class MatcherBase(object):

    """
    Base class for stanza matchers. Stanza matchers are used to pick
    stanzas out of the XML stream and pass them to the appropriate
    stream handlers.
    """

    def __init__(self, criteria):
        """
        Create a new stanza matcher.

        Arguments:
            criteria -- Object to compare some aspect of a stanza
                        against.
        """
        self._criteria = criteria

    def match(self, xml):
        """
        Check if a stanza matches the stored criteria.

        Meant to be overridden.
        """
        return False
