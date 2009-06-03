from . import base
import threading

class Callback(base.BaseHandler):
	
	def __init__(self, name, matcher, pointer, thread=False, once=False):
		base.BaseHandler.__init__(self, name, matcher)
		self._pointer = pointer
		self._thread = thread
		self._once = once
	
	def run(self, payload):
		base.BaseHandler.run(self, payload)
		if self._thread:
			x = threading.Thread(name="Callback_%s" % self.name, target=self._pointer, args=(payload,))
			x.start()
		else:
			self._pointer(payload)
		if self._once:
			self._destroy = True
