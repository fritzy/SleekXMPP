from . import base
import queue
import logging

class Waiter(base.BaseHandler):
	
	def __init__(self, name, matcher):
		base.BaseHandler.__init__(self, name, matcher)
		self._payload = queue.Queue()
	
	def prerun(self, payload):
		logging.debug("Putting into Waiter %s" % self.name)
		self._payload.put(payload)
	
	def run(self, payload):
		pass

	def wait(self, timeout=60):
		logging.debug("Waiting on %s." % self.name)
		try:
			return self._payload.get(True, timeout)
		except queue.Empty:
			logging.warning("Timed out waiting for %s" % self.name)
			return False
	
	def checkDelete(self):
		return True
