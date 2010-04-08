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
from . import base
import logging
from xml.etree import cElementTree as ET

class xep_0030(base.base_plugin):
	"""
	XEP-0030 Service Discovery
	"""
	
	def plugin_init(self):
		self.xep = '0030'
		self.description = 'Service Discovery'
		self.features = {'main': ['http://jabber.org/protocol/disco#info', 'http://jabber.org/protocol/disco#items']}
		self.identities = {'main': [{'category': 'client', 'type': 'pc', 'name': 'SleekXMPP'}]}
		self.items = {'main': []}
		self.xmpp.add_handler("<iq type='get' xmlns='%s'><query xmlns='http://jabber.org/protocol/disco#info' /></iq>" % self.xmpp.default_ns, self.info_handler)
		self.xmpp.add_handler("<iq type='get' xmlns='%s'><query xmlns='http://jabber.org/protocol/disco#items' /></iq>" % self.xmpp.default_ns, self.item_handler)
	
	def add_feature(self, feature, node='main'):
		if not node in self.features:
			self.features[node] = []
		self.features[node].append(feature)
	
	def add_identity(self, category=None, itype=None, name=None, node='main'):
		if not node in self.identities:
			self.identities[node] = []
		self.identities[node].append({'category': category, 'type': itype, 'name': name})
	
	def add_item(self, jid=None, name=None, node='main', subnode=''):
		if not node in self.items:
			self.items[node] = []
		self.items[node].append({'jid': jid, 'name': name, 'node': subnode})

	def info_handler(self, xml):
		logging.debug("Info request from %s" % xml.get('from', ''))
		iq = self.xmpp.makeIqResult(xml.get('id', self.xmpp.getNewId()))
		iq.attrib['from'] = xml.get('to')
		iq.attrib['to'] = xml.get('from', self.xmpp.server)
		query = xml.find('{http://jabber.org/protocol/disco#info}query')
		node = query.get('node', 'main')
		for identity in self.identities.get(node, []):
			idxml = ET.Element('identity')
			for attrib in identity:
				if identity[attrib]:
					idxml.attrib[attrib] = identity[attrib]
			query.append(idxml)
		for feature in self.features.get(node, []):
			featxml = ET.Element('feature')
			featxml.attrib['var'] = feature
			query.append(featxml)
		iq.append(query)
		#print ET.tostring(iq)
		self.xmpp.send(iq)

	def item_handler(self, xml):
		logging.debug("Item request from %s" % xml.get('from', ''))
		iq = self.xmpp.makeIqResult(xml.get('id', self.xmpp.getNewId()))
		iq.attrib['from'] = xml.get('to')
		iq.attrib['to'] = xml.get('from', self.xmpp.server)
		query = self.xmpp.makeIqQuery(iq, 'http://jabber.org/protocol/disco#items').find('{http://jabber.org/protocol/disco#items}query')
		node = xml.find('{http://jabber.org/protocol/disco#items}query').get('node', 'main')
		for item in self.items.get(node, []):
			itemxml = ET.Element('item')
			itemxml.attrib = item
			if itemxml.attrib['jid'] is None:
				itemxml.attrib['jid'] = xml.get('to')
			query.append(itemxml)
		self.xmpp.send(iq)
	
	def getItems(self, jid, node=None):
		iq = self.xmpp.makeIqGet()
		iq.attrib['from'] = self.xmpp.fulljid
		iq.attrib['to'] = jid
		self.xmpp.makeIqQuery(iq, 'http://jabber.org/protocol/disco#items')
		if node:
			iq.find('{http://jabber.org/protocol/disco#items}query').attrib['node'] = node
		return iq.send()
	
	def getInfo(self, jid, node=None):
		iq = self.xmpp.makeIqGet()
		iq.attrib['from'] = self.xmpp.fulljid
		iq.attrib['to'] = jid
		self.xmpp.makeIqQuery(iq, 'http://jabber.org/protocol/disco#info')
		if node:
			iq.find('{http://jabber.org/protocol/disco#info}query').attrib['node'] = node
		return iq.send()

	def parseInfo(self, xml):
		result = {'identity': {}, 'feature': []}
		for identity in xml.findall('{http://jabber.org/protocol/disco#info}query/{{http://jabber.org/protocol/disco#info}identity'):
			result['identity'][identity['name']] = identity.attrib
		for feature in xml.findall('{http://jabber.org/protocol/disco#info}query/{{http://jabber.org/protocol/disco#info}feature'):
			result['feature'].append(feature.get('var', '__unknown__'))
		return result
