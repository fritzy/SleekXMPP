"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
class MatcherBase(object):

	def __init__(self, criteria):
		self._criteria = criteria
	
	def match(self, xml):
		return False
