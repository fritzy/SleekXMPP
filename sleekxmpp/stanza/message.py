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

class Message(RootStanza):
	interfaces = set(('type', 'to', 'from', 'id', 'body', 'subject', 'mucroom', 'mucnick'))
	types = set((None, 'normal', 'chat', 'headline', 'error', 'groupchat'))
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
		if self['type'] == 'groupchat':
			self['to'] = self['to'].bare
		del self['id']
		if body is not None:
			self['body'] = body
		return self
	
	def getMucroom(self):
		if self['type'] == 'groupchat':
			return self['from'].bare
		else:
			return ''
	
	def setMucroom(self, value):
		pass
	
	def delMucroom(self):
		pass
	
	def getMucnick(self):
		if self['type'] == 'groupchat':
			return self['from'].resource
		else:
			return ''
	
	def setMucnick(self, value):
		pass
	
	def delMucnick(self):
		pass
