"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""

class BaseHandler(object):


	def __init__(self, name, matcher):
		self.name = name
		self._destroy = False
		self._payload = None
		self._matcher = matcher
	
	def match(self, xml):
		return self._matcher.match(xml)
	
	def prerun(self, payload):
		self._payload = payload

	def run(self, payload):
		self._payload = payload
	
	def checkDelete(self):
		return self._destroy
