from .. xmlstream.stanzabase import StanzaBase
from xml.etree import cElementTree as ET

class Iq(StanzaBase):
	interfaces = set(('type', 'to', 'from', 'id', 'body', 'subject'))
	types = set(('get', 'result', 'set', 'error'))
	name = 'iq'
	namespace = 'jabber:client'

	def __init__(self, *args, **kwargs):
		StanzaBase.__init__(self, *args, **kwargs)
		if self['id'] == '':
			self['id'] = self.stream.getId()
		print("________LOADED IQ CLASS")
	
	def result(self):
		self['type'] = 'result'
		return self
	
	def set(self):
		self['type'] = 'set'
		return self
	
	def error(self):
		#TODO add error payloads
		self['type'] = 'error'
		return self
	
	def get(self):
		self['type'] = 'get'
		return self
	
	def setPayload(self, value):
		self.clear()
		StanzaBase.setPayload(self, value)
	
	def unhandled(self):
		pass
		# returned unhandled error
