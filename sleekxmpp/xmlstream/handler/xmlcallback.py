import threading
from . callback import Callback

class XMLCallback(Callback):
	
	def run(self, payload):
		Callback.run(self, payload.xml)
