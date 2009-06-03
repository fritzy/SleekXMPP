from __future__ import absolute_import
from sleekxmpp.xmlstream.matcher.xpath import MatchXPath

class StanzaBase(object):

	MATCHER = MatchXPath("")

	def __init__(self, stream, xml=None, extensions=[]):
		self.extensions = extensions
		self.p = {} #plugins

		self.xml = xml
		self.stream = stream
		if xml is not None:
			self.fromXML(xml)
	
	def fromXML(self, xml):
		"Initialize based on incoming XML"
		self._processXML(xml)
		for ext in self.extensions:
			ext.fromXML(self, xml)
		
	
	def _processXML(self, xml, cur_ns=''):
		if '}' in xml.tag:
			ns,tag = xml.tag[1:].split('}')
		else:
			tag = xml.tag
	
	def toXML(self, xml):
		"Set outgoing XML"
	
	def extend(self, extension_class, xml=None):
		"Initialize extension"
	
	def match(self, xml):
		return self.MATCHER.match(xml)
