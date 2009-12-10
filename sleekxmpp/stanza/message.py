from .. xmlstream.stanzabase import StanzaBase
from xml.etree import cElementTree as ET

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
	
if __name__ == '__main__':
	m = Message()
	m['to'] = 'me'
	m['from'] = 'you'
	m['type'] = 'chat'
	m.reply()
	m['body'] = 'Hello there!'
	m['subject'] = 'whatever'
	m['id'] = 'abc'
	print(str(m))
	print(m['body'])
	print(m['subject'])
	print(m['id'])
	m['type'] = None
	m['body'] = None
	m['id'] = None
	print(str(m))
	print(m['type'])
