from .. xmlstream.stanzabase import StanzaBase
from .. xmlstream import xmlstream as xmlstreammod
from .. xmlstream.matcher.xpath import MatchXPath

#_bases = [StanzaBase] + xmlstreammod.stanza_extensions.get('PresenceStanza', [])

#class PresenceStanza(*_bases):
class PresenceStanza(StanzaBase):
	
	def __init__(self, stream, xml=None):
		self.pfrom = ''
		self.pto = ''
		StanzaBase.__init__(self, stream, xml, xmlstreammod.stanza_extensions.get('PresenceStanza', []))

	def fromXML(self, xml):
		StanzaBase.fromXML(self, xml)
		self.pfrom = xml.get('from')
		self.pto = xml.get('to')
		self.ptype = xml.get('type')

stanzas = ({'stanza_class': PresenceStanza, 'matcher': MatchXPath('{jabber:client}presence'), 'root': True},)
