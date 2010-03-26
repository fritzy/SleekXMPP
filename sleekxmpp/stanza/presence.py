"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from .. xmlstream.stanzabase import StanzaBase
from xml.etree import cElementTree as ET
from . error import Error
from . rootstanza import RootStanza

class Presence(RootStanza):
	interfaces = set(('type', 'to', 'from', 'id', 'status', 'priority'))
	types = set(('available', 'unavailable', 'error', 'probe', 'subscribe', 'subscribed', 'unsubscribe', 'unsubscribed'))
	showtypes = set(('dnd', 'chat', 'xa', 'away'))
	sub_interfaces = set(('status', 'priority'))
	name = 'presence'
	namespace = 'jabber:client'

	def getShowElement(self):
		return self.xml.find("{%s}show" % self.namespace)

	def setType(self, value):
		show = self.getShowElement()
		if value in self.types:
			if show is not None:
				self.xml.remove(show)
			if value == 'available':
				value = ''
			self._setAttr('type', value)
		elif value in self.showtypes:
			if show is None:
				show = ET.Element("{%s}show" % self.namespace)
				self.xml.append(show)
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
	
	def reply(self):
		if self['type'] == 'unsubscribe':
			self['type'] = 'unsubscribed'
		elif self['type'] == 'subscribe':
			self['type'] = 'subscribed'
		return StanzaBase.reply(self)
