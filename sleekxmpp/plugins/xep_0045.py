"""
	SleekXMPP: The Sleek XMPP Library
	Copyright (C) 2007  Nathanael C. Fritz
	This file is part of SleekXMPP.

	SleekXMPP is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 2 of the License, or
	(at your option) any later version.

	SleekXMPP is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with SleekXMPP; if not, write to the Free Software
	Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""
from __future__ import with_statement
from . import base
import logging
from xml.etree import cElementTree as ET
from .. xmlstream.stanzabase import ElementBase, JID
from .. stanza.presence import Presence
from .. xmlstream.handler.callback import Callback
from .. xmlstream.matcher.xpath import MatchXPath
from .. xmlstream.matcher.xmlmask import MatchXMLMask

class MUCPresence(ElementBase):
	name = 'x'
	namespace = 'http://jabber.org/protocol/muc#user'
	plugin_attrib = 'muc'
	interfaces = set(('affiliation', 'role', 'jid', 'nick', 'room'))
	affiliations = set(('', ))
	roles = set(('', ))

	def getXMLItem(self):
		item = self.xml.find('{http://jabber.org/protocol/muc#user}item')
		if item is None:
			item = ET.Element('{http://jabber.org/protocol/muc#user}item')
			self.xml.append(item)
		return item

	def getAffiliation(self):
		#TODO if no affilation, set it to the default and return default
		item = self.getXMLItem()
		return item.get('affiliation', '')
	
	def setAffiliation(self, value):
		item = self.getXMLItem()
		#TODO check for valid affiliation
		item.attrib['affiliation'] = value
		return self
	
	def delAffiliation(self):
		item = self.getXMLItem()
		#TODO set default affiliation
		if 'affiliation' in item.attrib: del item.attrib['affiliation']
		return self
	
	def getJid(self):
		item = self.getXMLItem()
		return JID(item.get('jid', ''))
	
	def setJid(self, value):
		item = self.getXMLItem()
		if not isinstance(value, str):
			value = str(value)
		item.attrib['jid'] = value
		return self
	
	def delJid(self):
		item = self.getXMLItem()
		if 'jid' in item.attrib: del item.attrib['jid']
		return self
		
	def getRole(self):
		item = self.getXMLItem()
		#TODO get default role, set default role if none
		return item.get('role', '')
	
	def setRole(self, value):
		item = self.getXMLItem()
		#TODO check for valid role
		item.attrib['role'] = value
		return self
	
	def delRole(self):
		item = self.getXMLItem()
		#TODO set default role
		if 'role' in item.attrib: del item.attrib['role']
		return self
	
	def getNick(self):
		return self.parent()['from'].resource
	
	def getRoom(self):
		return self.parent()['from'].bare
	
	def setNick(self, value):
		logging.warning("Cannot set nick through mucpresence plugin.")
		return self
	
	def setRoom(self, value):
		logging.warning("Cannot set room through mucpresence plugin.")
		return self
	
	def delNick(self):
		logging.warning("Cannot delete nick through mucpresence plugin.")
		return self
	
	def delRoom(self):
		logging.warning("Cannot delete room through mucpresence plugin.")
		return self

class xep_0045(base.base_plugin):
	"""
	Impliments XEP-0045 Multi User Chat
	"""
	
	def plugin_init(self):
		self.rooms = {}
		self.ourNicks = {}
		self.xep = '0045'
		self.description = 'Multi User Chat'
		# load MUC support in presence stanzas
		self.xmpp.stanzaPlugin(Presence, MUCPresence)
		self.xmpp.registerHandler(Callback('MUCPresence', MatchXMLMask("<presence xmlns='%s' />" % self.xmpp.default_ns), self.handle_groupchat_presence))
		self.xmpp.registerHandler(Callback('MUCMessage', MatchXMLMask("<message xmlns='%s' type='groupchat'><body/></message>" % self.xmpp.default_ns), self.handle_groupchat_message))
	
	def handle_groupchat_presence(self, pr):
		""" Handle a presence in a muc.
		"""
		if pr['muc']['room'] not in self.rooms.keys():
			return
		entry = pr['muc'].getValues()
		if pr['type'] == 'unavailable':
			del self.rooms[entry['room']][entry['nick']]
		else:
			self.rooms[entry['room']][entry['nick']] = entry
		logging.debug("MUC presence from %s/%s : %s" % (entry['room'],entry['nick'], entry))
		self.xmpp.event("groupchat_presence", pr)
	
	def handle_groupchat_message(self, msg):
		""" Handle a message event in a muc.
		"""
		self.xmpp.event('groupchat_message', msg)
		       
	def jidInRoom(self, room, jid):
		for nick in self.rooms[room]:
			entry = self.rooms[room][nick]
			if entry is not None and entry['jid'].full == jid:
				return True
		return False

	def getRoomForm(self, room, ifrom=None):
		iq = self.xmpp.makeIqGet()
		iq['to'] = room
		if ifrom is not None:
			iq['from'] = ifrom
		query = ET.Element('{http://jabber.org/protocol/muc#owner}query')
		iq.append(query)
		result = iq.send()
		if result['type'] == 'error':
			return False
		xform = result.xml.find('{http://jabber.org/protocol/muc#owner}query/{jabber:x:data}x')
		if xform is None: return False
		form = self.xmpp.plugin['xep_0004'].buildForm(xform)
		return form
	
	def configureRoom(self, room, form=None, ifrom=None):
		if form is None:
			form = self.getRoomForm(room, ifrom=ifrom)
			#form = self.xmpp.plugin['xep_0004'].makeForm(ftype='submit')
			#form.addField('FORM_TYPE', value='http://jabber.org/protocol/muc#roomconfig')	
		iq = self.xmpp.makeIqSet()
		iq['to'] = room
		if ifrom is not None:
			iq['from'] = ifrom
		query = ET.Element('{http://jabber.org/protocol/muc#owner}query')
		form = form.getXML('submit')
		query.append(form)
		iq.append(query)
		result = iq.send()
		if result['type'] == 'error':
			return False
		return True
	
	def joinMUC(self, room, nick, maxhistory="0", password='', wait=False, pstatus=None, pshow=None):
		""" Join the specified room, requesting 'maxhistory' lines of history.
		"""
		stanza = self.xmpp.makePresence(pto="%s/%s" % (room, nick), pstatus=pstatus, pshow=pshow)
		x = ET.Element('{http://jabber.org/protocol/muc}x')
		if password:
			passelement = ET.Element('password')
			passelement.text = password
			x.append(passelement)
		history = ET.Element('history')
		history.attrib['maxstanzas'] = maxhistory
		x.append(history)
		stanza.append(x)
		if not wait:
			self.xmpp.send(stanza)
		else:
			#wait for our own room presence back
			expect = ET.Element("{%s}presence" % self.xmpp.default_ns, {'from':"%s/%s" % (room, nick)})
			self.xmpp.send(stanza, expect)
		self.rooms[room] = {}
		self.ourNicks[room] = nick
	
	def destroy(self, room, reason='', altroom = '', ifrom=None):
		iq = self.xmpp.makeIqSet()
		if ifrom is not None:
			iq['from'] = ifrom
		iq['to'] = room
		query = ET.Element('{http://jabber.org/protocol/muc#owner}query')
		destroy = ET.Element('destroy')
		if altroom:
			destroy.attrib['jid'] = altroom
		xreason = ET.Element('reason')
		xreason.text = reason
		destroy.append(xreason)
		query.append(destroy)
		iq.append(query)
		r = iq.send()
		if r is False or r['type'] == 'error':
			return False
		return True

	def setAffiliation(self, room, jid=None, nick=None, affiliation='member'):
		""" Change room affiliation."""
		if affiliation not in ('outcast', 'member', 'admin', 'owner', 'none'):
			raise TypeError
		query = ET.Element('{http://jabber.org/protocol/muc#admin}query')
		if nick is not None:
			item = ET.Element('item', {'affiliation':affiliation, 'nick':nick})	
		else:
			item = ET.Element('item', {'affiliation':affiliation, 'jid':jid})	
		query.append(item)
		iq = self.xmpp.makeIqSet(query)
		iq['to'] = room
		result = iq.send()
		if result is False or result['type'] != 'result':
			raise ValueError
		return True
	
	def invite(self, room, jid, reason=''):
		""" Invite a jid to a room."""
		msg = self.xmpp.makeMessage(room)
		msg['from'] = self.xmpp.jid
		x = ET.Element('{http://jabber.org/protocol/muc#user}x')
		invite = ET.Element('{http://jabber.org/protocol/muc#user}invite', {'to': jid})
		if reason:
			rxml = ET.Element('reason')
			rxml.text = reason
			invite.append(rxml)
		x.append(invite)
		msg.append(x)
		self.xmpp.send(msg)

	def leaveMUC(self, room, nick):
		""" Leave the specified room.
		"""
		self.xmpp.sendPresence(pshow='unavailable', pto="%s/%s" % (room, nick))
		del self.rooms[room]
	
	def getRoomConfig(self, room):
		iq = self.xmpp.makeIqGet('http://jabber.org/protocol/muc#owner')
		iq['to'] = room
		result = iq.send()
		if result is None or result['type'] != 'result':
			raise ValueError
		form = result.xml.find('{http://jabber.org/protocol/muc#owner}query/{jabber:x:data}x')
		if form is None:
			raise ValueError
		return self.xmpp.plugin['xep_0004'].buildForm(form)
	
	def cancelConfig(self, room):
		query = ET.Element('{http://jabber.org/protocol/muc#owner}query')
		x = ET.Element('{jabber:x:data}x', type='cancel')
		query.append(x)
		iq = self.xmpp.makeIqSet(query)
		iq.send()
	
	def setRoomConfig(self, room, config):
		query = ET.Element('{http://jabber.org/protocol/muc#owner}query')
		x = config.getXML('submit')
		query.append(x)
		iq = self.xmpp.makeIqSet(query)
		iq['to'] = room
		iq.send()
		
	def getJoinedRooms(self):
		return self.rooms.keys()
		
	def getOurJidInRoom(self, roomJid):
		""" Return the jid we're using in a room.
		"""
		return "%s/%s" % (roomJid, self.ourNicks[roomJid])
		
	def getJidProperty(self, room, nick, jidProperty):
		""" Get the property of a nick in a room, such as its 'jid' or 'affiliation'
			If not found, return None.
		"""
		if room in self.rooms and nick in self.rooms[room] and jidProperty in self.rooms[room][nick]:
			return self.rooms[room][nick][jidProperty]
		else:
			return None
	
	def getRoster(self, room):
		""" Get the list of nicks in a room.
		"""
		if room not in self.rooms.keys():
			return None
		return self.rooms[room].keys()
