"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from .. xmlstream.stanzabase import ElementBase, ET, JID
import logging

class Roster(ElementBase):
	namespace = 'jabber:iq:roster'
	name = 'query'
	plugin_attrib = 'roster'
	interfaces = set(('items',))
	sub_interfaces = set()

	def setItems(self, items):
		self.delItems()
		for jid in items:
			ijid = str(jid)
			item = ET.Element('{jabber:iq:roster}item', {'jid': ijid})
			if 'subscription' in items[jid]:
				item.attrib['subscription'] = items[jid]['subscription']
			if 'name' in items[jid]:
				item.attrib['name'] = items[jid]['name']
			if 'groups' in items[jid]:
				for group in items[jid]['groups']:
					groupxml = ET.Element('{jabber:iq:roster}group')
					groupxml.text = group
					item.append(groupxml)
			self.xml.append(item)
		return self
	
	def getItems(self):
		items = {}
		itemsxml = self.xml.findall('{jabber:iq:roster}item')
		if itemsxml is not None:
			for itemxml in itemsxml:
				item = {}
				item['name'] = itemxml.get('name', '')
				item['subscription'] = itemxml.get('subscription', '')
				item['groups'] = []
				groupsxml = itemxml.findall('{jabber:iq:roster}group')
				if groupsxml is not None:
					for groupxml in groupsxml:
						item['groups'].append(groupxml.text)
				items[itemxml.get('jid')] = item
		return items
	
	def delItems(self):
		for child in self.xml.getchildren():
			self.xml.remove(child)
