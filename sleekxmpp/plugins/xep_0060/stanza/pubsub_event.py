from sleekxmpp.xmlstream.stanzabase import registerStanzaPlugin, ElementBase, ET, JID
from sleekxmpp.stanza.iq import Iq
from sleekxmpp.stanza.message import Message
from sleekxmpp.basexmpp import basexmpp
from sleekxmpp.xmlstream.xmlstream import XMLStream
import logging
from sleekxmpp.plugins import xep_0004

class Event(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'event'
	plugin_attrib = 'pubsub_event'
	interfaces = set(('node',))
	plugin_attrib_map = {}
	plugin_tag_map = {}

registerStanzaPlugin(Message, Event)

class EventItem(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'item'
	plugin_attrib = 'item'
	interfaces = set(('id', 'payload'))
	plugin_attrib_map = {}
	plugin_tag_map = {}

	def setPayload(self, value):
		self.xml.append(value)
	
	def getPayload(self):
		childs = self.xml.getchildren()
		if len(childs) > 0:
			return childs[0]
	
	def delPayload(self):
		for child in self.xml.getchildren():
			self.xml.remove(child)


class EventRetract(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'retract'
	plugin_attrib = 'retract'
	interfaces = set(('id',))
	plugin_attrib_map = {}
	plugin_tag_map = {}

class EventItems(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'items'
	plugin_attrib = 'items'
	interfaces = set(('node',))
	plugin_attrib_map = {}
	plugin_tag_map = {}
	subitem = (EventItem, EventRetract)

registerStanzaPlugin(Event, EventItems)

class EventCollection(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'collection'
	plugin_attrib = name
	interfaces = set(('node',))
	plugin_attrib_map = {}
	plugin_tag_map = {}

registerStanzaPlugin(Event, EventCollection)

class EventAssociate(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'associate'
	plugin_attrib = name
	interfaces = set(('node',))
	plugin_attrib_map = {}
	plugin_tag_map = {}

registerStanzaPlugin(EventCollection, EventAssociate)

class EventDisassociate(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'disassociate'
	plugin_attrib = name
	interfaces = set(('node',))
	plugin_attrib_map = {}
	plugin_tag_map = {}

registerStanzaPlugin(EventCollection, EventDisassociate)

class EventConfiguration(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'configuration'
	plugin_attrib = name
	interfaces = set(('node', 'config'))
	plugin_attrib_map = {}
	plugin_tag_map = {}
	
registerStanzaPlugin(Event, EventConfiguration)
registerStanzaPlugin(EventConfiguration, xep_0004.Form)

class EventPurge(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'purge'
	plugin_attrib = name
	interfaces = set(('node',))
	plugin_attrib_map = {}
	plugin_tag_map = {}

registerStanzaPlugin(Event, EventPurge)

class EventSubscription(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'subscription'
	plugin_attrib = name
	interfaces = set(('node','expiry', 'jid', 'subid', 'subscription'))
	plugin_attrib_map = {}
	plugin_tag_map = {}
	
	def setJid(self, value):
		self._setAttr('jid', str(value))
	
	def getJid(self):
		return JID(self._getAttr('jid'))

registerStanzaPlugin(Event, EventSubscription)
