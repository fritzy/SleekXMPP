from . import base
from xml.etree import cElementTree

class MatchXPath(base.MatcherBase):

	def match(self, xml):
		x = cElementTree.Element('x')
		x.append(xml)
		if x.find(self._criteria) is not None:
			return True
		return False
