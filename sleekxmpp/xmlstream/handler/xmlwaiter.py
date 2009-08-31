from . waiter import Waiter

class XMLWaiter(Waiter):
	
	def prerun(self, payload):
		Waiter.prerun(self, payload.xml)
