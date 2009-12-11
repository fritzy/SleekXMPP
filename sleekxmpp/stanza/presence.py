from .. xmlstream.stanzabase import StanzaBase
from xml.etree import cElementTree as ET
from . error import Error

class Presence(StanzaBase):
	interfaces = set(('type', 'to', 'from', 'id', 'status', 'priority'))
	types = set(('available', 'unavailable', 'error', 'probe', 'subscribe', 'subscribed', 'unsubscribe', 'unsubscribed'))
	showtypes = set(('dnd', 'ffc', 'xa', 'away'))
	sub_interfaces = set(('status', 'priority'))
	name = 'presence'
	namespace = 'jabber:client'

	def getShowElement(self):
		return self.xml.find("{%s}show" % self.namespace)

	def setType(self, value):
		if value in self.types:
			show = self.getShowElement()
			if value in self.types:
				if show is not None:
					self.xml.remove(show)
				self._setAttr('type', value)
			elif value in self.showtypes:
				if show is None:
					show = ET.Element("{%s}show" % self.namespace)
				show.text = value
		return self

	def setPriority(self, value):
		self._setSubText('priority', str(value))
	
	def getPriority(self):
		p = self._getSubText('priority')
		if not p: p = 0
		return int(p)
	
	def getType(self):
		out = self._getAttr('type')
		if not out:
			show = self.getShowElement()
			if show is not None:
				out = show.text
		if not out or out is None:
			out = 'available'
		return out
	
	def delType(self):
		self.setType('available')

Presence.plugin_attrib_map['error'] = Error
Presence.plugin_tag_map["{%s}%s" % (Error.namespace, Error.name)] = Error
