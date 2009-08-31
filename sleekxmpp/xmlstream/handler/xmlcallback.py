import threading
from . callback import Callback

class XMLCallback(Callback):
	
	def run(self, payload, instream=False):
		Callback.run(self, payload.xml, instream)
