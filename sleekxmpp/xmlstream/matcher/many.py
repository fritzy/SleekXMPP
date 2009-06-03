from . import base
from xml.etree import cElementTree

class MatchMany(base.MatcherBase):

	def match(self, xml):
		for m in self._criteria:
			if m.match(xml):
				return True
		return False
