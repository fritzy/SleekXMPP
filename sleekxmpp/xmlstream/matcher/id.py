from . import base

class MatcherId(base.MatcherBase):
	
	def match(self, xml):
		return xml.get('id') == self._criteria
