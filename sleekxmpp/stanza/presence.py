"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from . error import Error
from . rootstanza import RootStanza
from .. xmlstream.stanzabase import StanzaBase, ET


class Presence(RootStanza):
	interfaces = set(('type', 'to', 'from', 'id', 'show', 'status', 'priority'))
	types = set(('available', 'unavailable', 'error', 'probe', 'subscribe', 'subscribed', 'unsubscribe', 'unsubscribed'))
	showtypes = set(('dnd', 'chat', 'xa', 'away'))
	sub_interfaces = set(('show', 'status', 'priority'))
	name = 'presence'
	plugin_attrib = name
	namespace = 'jabber:client'

	def setShow(self, show):
		if show in self.showtypes:
			self._setSubText('show', text=show)
		return self

	def setType(self, value):
		if value in self.types:
			self['show'] = None
			if value == 'available':
				value = ''
			self._setAttr('type', value)
		elif value in self.showtypes:
			self['show'] = value
		return self

	def setPriority(self, value):
		self._setSubText('priority', text = str(value))
	
	def getPriority(self):
		p = self._getSubText('priority')
		if not p: p = 0
		return int(p)
	
	def getType(self):
		out = self._getAttr('type')
		if not out:
			out = self['show']
		if not out or out is None:
			out = 'available'
		return out
	
	def reply(self):
		if self['type'] == 'unsubscribe':
			self['type'] = 'unsubscribed'
		elif self['type'] == 'subscribe':
			self['type'] = 'subscribed'
		return StanzaBase.reply(self)
