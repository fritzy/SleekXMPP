from . import base

class MatcherId(base.MatcherBase):
	
	def match(self, xml):
		return xml['id'] == self._criteria
