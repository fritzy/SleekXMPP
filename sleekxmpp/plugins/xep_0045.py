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

class xep_0045(base.base_plugin):
	"""
	Impliments XEP-0045 Multi User Chat
	"""
	
	def plugin_init(self):
		self.rooms = {}
		self.ourNicks = {}
		self.xep = '0045'
		self.description = 'Multi User Chat (Very Basic Still)'
		self.xmpp.add_handler("<message xmlns='%s' type='groupchat'><body/></message>" % self.xmpp.default_ns, self.handle_groupchat_message)
		self.xmpp.add_handler("<presence />", self.handle_groupchat_presence)
	
	def handle_groupchat_presence(self, xml):
		""" Handle a presence in a muc.
		"""
		source = xml.attrib['from']
		room = self.xmpp.getjidbare(source)
		if room not in self.rooms.keys():
			return
		nick = self.xmpp.getjidresource(source)
		entry = {
				'nick': nick,
				'room': room,
		}
		if 'type' in xml.attrib.keys():
			entry['type'] = xml.attrib['type']
		for tag in ['status','show','priority']:
			if xml.find(('{%s}' % self.xmpp.default_ns) + tag) != None:
				entry[tag] = xml.find(('{%s}' % self.xmpp.default_ns) + tag).text
			else:
				entry[tag] = None
		
		for tag in ['affiliation','role','jid']:
			item = xml.find('{http://jabber.org/protocol/muc#user}x/{http://jabber.org/protocol/muc#user}item')
			if item != None:
				if tag in item.attrib:
					entry[tag] = item.attrib[tag]
				else:
					entry[tag] = None
			else:
				entry[tag] = None
		
		if entry['status'] == 'unavailable':
			self.rooms[room][nick] = None
		else:
			self.rooms[room][nick] = entry
		logging.debug("MUC presence from %s/%s : %s" % (entry['room'],entry['nick'], entry))
		self.xmpp.event("groupchat_presence", entry)
	
	def handle_groupchat_message(self, xml):
		""" Handle a message event in a muc.
		"""
		mfrom = xml.attrib['from']
		message = xml.find('{%s}body' % self.xmpp.default_ns).text
		subject = xml.find('{%s}subject' % self.xmpp.default_ns)
		if subject:
			subject = subject.text
		else:
			subject = ''
		resource = self.xmpp.getjidresource(mfrom)
		mfrom = self.xmpp.getjidbare(mfrom)
		mtype = xml.attrib.get('type', 'normal')
		self.xmpp.event("groupchat_message", {'room': mfrom, 'name': resource, 'type': mtype, 'subject': subject, 'message': message})
	
	def joinMUC(self, room, nick, maxhistory="0", password='', wait=False):
		""" Join the specified room, requesting 'maxhistory' lines of history.
		"""
		stanza = self.xmpp.makePresence(pto="%s/%s" % (room, nick))
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
			expect = ET.Element('{jabber:client}presence', {'from':"%s/%s" % (room, nick)})
			self.xmpp.send(stanza, expect)
		self.rooms[room] = {}
		self.ourNicks[room] = nick
	
	def setAffiliation(self, room, jid, affiliation='member'):
		""" Change room affiliation."""
		if affiliation not in ('outcast', 'member', 'admin', 'owner', 'none'):
			raise TypeError
		query = ET.Element('{http://jabber.org/protocol/muc#admin}query')
		item = ET.Element('item', {'affiliation':affiliation, 'jid':jid})	
		query.append(item)
		iq = self.xmpp.makeIqSet(query)
		iq.attrib['to'] = room
		result = self.xmpp.send(iq, "<iq id='%s' />" % iq.get('id'))
		if result is None or result.get('type') != 'result':
			raise ValueError
		return True
	
	def invite(self, room, jid, reason=''):
		""" Invite a jid to a room."""
		msg = self.xmpp.makeMessage(room, mtype='none')
		x = ET.Element('{http://jabber.org/protocol/muc#user}x')
		invite = ET.Element('invite', {'to': jid})
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
		iq.attrib['to'] = room
		result = self.xmpp.send(iq, "<iq id='%s' />" % iq.get('id'))
		if result is None or result.get('type') != 'result':
			raise ValueError
		form = result.find('{http://jabber.org/protocol/muc#owner}query/{jabber:x:data}x')
		if form is None:
			raise ValueError
		return self.xmpp.plugin['xep_0004'].buildForm(form)
	
	def cancelConfig(self, room):
		query = ET.Element('{http://jabber.org/protocol/muc#owner}query')
		x = ET.Element('{jabber:x:data}x', type='cancel')
		query.append(x)
		iq = self.xmpp.makeIqSet(query)
		self.xmpp.send(iq, "<iq id='%s' />" % iq.get('id'))
	
	def setRoomConfig(self, room, config):
		query = ET.Element('{http://jabber.org/protocol/muc#owner}query')
		x = config.getXML('submit')
		query.append(x)
		iq = self.xmpp.makeIqSet(query)
		iq.attrib['to'] = room
		self.xmpp.send(iq, "<iq id='%s' />" % iq.get('id'))
		
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
		if self.rooms.has_key(room) and self.rooms[room].has_key(nick) and self.rooms[room][nick].has_key(jidProperty):
			return self.rooms[room][nick][jidProperty]
		else:
			return None
	
	def getRoster(self, room):
		""" Get the list of nicks in a room.
		"""
		if room not in self.rooms.keys():
			return None
		return self.rooms[room].keys()
