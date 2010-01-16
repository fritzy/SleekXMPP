from . import base
from xml.etree import cElementTree

class StanzaPath(base.MatcherBase):

	def match(self, stanza):
		return stanza.match(self._criteria)
