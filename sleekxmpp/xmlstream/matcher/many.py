"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from . import base
from xml.etree import cElementTree

class MatchMany(base.MatcherBase):

	def match(self, xml):
		for m in self._criteria:
			if m.match(xml):
				return True
		return False
