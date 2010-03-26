"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from . import base
import logging

class Callback(base.BaseHandler):
	
	def __init__(self, name, matcher, pointer, thread=False, once=False, instream=False):
		base.BaseHandler.__init__(self, name, matcher)
		self._pointer = pointer
		self._thread = thread
		self._once = once
		self._instream = instream

	def prerun(self, payload):
		base.BaseHandler.prerun(self, payload)
		if self._instream:
			self.run(payload, True)
	
	def run(self, payload, instream=False):
		if not self._instream or instream:
			base.BaseHandler.run(self, payload)
			#if self._thread:
			#	x = threading.Thread(name="Callback_%s" % self.name, target=self._pointer, args=(payload,))
			#	x.start()
			#else:
			self._pointer(payload)
			if self._once:
				self._destroy = True
