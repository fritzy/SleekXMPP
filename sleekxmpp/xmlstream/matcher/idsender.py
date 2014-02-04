# -*- coding: utf-8 -*-
"""
    sleekxmpp.xmlstream.matcher.id
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Part of SleekXMPP: The Sleek XMPP Library

    :copyright: (c) 2011 Nathanael C. Fritz
    :license: MIT, see LICENSE for more details
"""

from sleekxmpp.xmlstream.matcher.base import MatcherBase


class MatchIDSender(MatcherBase):

    """
    The IDSender matcher selects stanzas that have the same stanza 'id'
    interface value as the desired ID, and that the 'from' value is one
    of a set of approved entities that can respond to a request.
    """

    def match(self, xml):
        """Compare the given stanza's ``'id'`` attribute to the stored
        ``id`` value, and verify the sender's JID.

        :param xml: The :class:`~sleekxmpp.xmlstream.stanzabase.ElementBase`
                    stanza to compare against.
        """

        selfjid = self._criteria['self']
        peerjid = self._criteria['peer']

        allowed = {}
        allowed[''] = True
        allowed[selfjid.bare] = True
        allowed[selfjid.host] = True
        allowed[peerjid.full] = True
        allowed[peerjid.bare] = True
        allowed[peerjid.host] = True

        _from = xml['from']

        try:
            return xml['id'] == self._criteria['id'] and allowed[_from]
        except KeyError:
            return False
