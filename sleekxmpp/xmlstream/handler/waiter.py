from . import base
import Queue
import logging

class Waiter(base.BaseHandler):
	
	def __init__(self, name, matcher):
		base.BaseHandler.__init__(self, name, matcher)
		self._payload = Queue.Queue()
	
	def run(self, payload):
		self._payload.put(payload)

	def wait(self, timeout=60):
		try:
			return self._payload.get(True, timeout)
		except Queue.Empty:
			return False
	
	def checkDelete(self):
		return True
