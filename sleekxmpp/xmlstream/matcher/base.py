
class MatcherBase(object):

	def __init__(self, criteria):
		self._criteria = criteria
	
	def match(self, xml):
		return False
