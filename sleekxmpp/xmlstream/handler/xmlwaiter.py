from . waiter import Waiter

class XMLWaiter(Waiter):
	
	def run(self, payload):
		Waiter.run(self, payload.xml)
