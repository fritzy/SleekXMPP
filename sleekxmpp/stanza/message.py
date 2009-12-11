from .. xmlstream.stanzabase import StanzaBase
from xml.etree import cElementTree as ET
from . error import Error

class Message(StanzaBase):
	interfaces = set(('type', 'to', 'from', 'id', 'body', 'subject'))
	types = set((None, 'normal', 'chat', 'headline', 'error'))
	sub_interfaces = set(('body', 'subject'))
	name = 'message'
	namespace = 'jabber:client'

	def getType(self):
		return self.xml.attrib.get('type', 'normal')
	
	def chat(self):
		self['type'] = 'chat'
		return self
	
	def normal(self):
		self['type'] = 'normal'
		return self
	
	def reply(self, body=None):
		StanzaBase.reply(self)
		if body is not None:
			self['body'] = body
		return self
	
Message.plugin_attrib_map['error'] = Error
Message.plugin_tag_map["{%s}%s" % (Error.namespace, Error.name)] = Error
