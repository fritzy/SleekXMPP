from .. xmlstream.stanzabase import StanzaBase
from xml.etree import cElementTree as ET
from . error import Error
from .. xmlstream.handler.waiter import Waiter
from .. xmlstream.matcher.id import MatcherId
from . rootstanza import RootStanza

class Iq(RootStanza):
	interfaces = set(('type', 'to', 'from', 'id','query'))
	types = set(('get', 'result', 'set', 'error'))
	name = 'iq'
	namespace = 'jabber:client'

	def __init__(self, *args, **kwargs):
		StanzaBase.__init__(self, *args, **kwargs)
		if self['id'] == '':
			if self.stream is not None:
				self['id'] = self.stream.getNewId()
			else:
				self['id'] = '0'
	
	def unhandled(self):
		self.reply()
		self['error']['condition'] = 'feature-not-implemented'
		self['error']['text'] = 'No handlers registered for this request.'
		self.send()
	
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
	
	def setQuery(self, value):
		query = self.xml.find("{%s}query" % value)
		if query is None and value:
			self.clear()
			query = ET.Element("{%s}query" % value)
			self.xml.append(query)
		return self
	
	def getQuery(self):
		for child in self.xml.getchildren():
			if child.tag.endswith('query'):
				ns =child.tag.split('}')[0]
				if '{' in ns:
					ns = ns[1:]
				return ns
		return ''
	
	def reply(self):
		self['type'] = 'result'
		StanzaBase.reply(self)
		return self
	
	def delQuery(self):
		for child in self.getchildren():
			if child.tag.endswith('query'):
				self.xml.remove(child)
		return self
	
	def send(self, block=True, timeout=10):
		if block and self['type'] in ('get', 'set'):
			waitfor = Waiter('IqWait_%s' % self['id'], MatcherId(self['id']))
			self.stream.registerHandler(waitfor)
			StanzaBase.send(self)
			return waitfor.wait(timeout)
		else:
			return StanzaBase.send(self)
