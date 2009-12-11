from .. xmlstream.stanzabase import StanzaBase
from xml.etree import cElementTree as ET
from . error import Error
from .. xmlstream.handler.waiter import Waiter
from .. xmlstream.matcher.id import MatcherId

class Iq(StanzaBase):
	interfaces = set(('type', 'to', 'from', 'id', 'body', 'subject'))
	types = set(('get', 'result', 'set', 'error'))
	name = 'iq'
	namespace = 'jabber:client'

	def __init__(self, *args, **kwargs):
		StanzaBase.__init__(self, *args, **kwargs)
		if self['id'] == '':
			self['id'] = self.stream.getId()
	
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
	
	def exception(self, traceback=None):
		pass
	
	def send(self, block=True, timeout=10):
		if block:
			waitfor = Waiter('IqWait_%s' % self['id'], MatcherId(self['id']))
			self.stream.registerHandler(waitfor)
			StanzaBase.send(self)
			return waitfor.wait(timeout)
		else:
			return StanzaBase.send(self)
		

Iq.plugin_attrib_map['error'] = Error
Iq.plugin_tag_map["{%s}%s" % (Error.namespace, Error.name)] = Error
