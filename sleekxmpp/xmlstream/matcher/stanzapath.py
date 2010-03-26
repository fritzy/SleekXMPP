"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from . import base
from xml.etree import cElementTree

class StanzaPath(base.MatcherBase):

	def match(self, stanza):
		return stanza.match(self._criteria)
