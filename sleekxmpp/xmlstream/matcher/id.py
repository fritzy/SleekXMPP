"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from . import base

class MatcherId(base.MatcherBase):
	
	def match(self, xml):
		return xml['id'] == self._criteria
