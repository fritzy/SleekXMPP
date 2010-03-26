"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from . import base
try:
	import queue
except ImportError:
	import Queue as queue
import logging
from .. stanzabase import StanzaBase

class Waiter(base.BaseHandler):
	
	def __init__(self, name, matcher):
		base.BaseHandler.__init__(self, name, matcher)
		self._payload = queue.Queue()
	
	def prerun(self, payload):
		self._payload.put(payload)
	
	def run(self, payload):
		pass

	def wait(self, timeout=60):
		try:
			return self._payload.get(True, timeout)
		except queue.Empty:
			logging.warning("Timed out waiting for %s" % self.name)
			return False
	
	def checkDelete(self):
		return True
