from .. xmlstream.stanzabase import ElementBase, ET, JID
from .. stanza.iq import Iq
from .. stanza.message import Message
from .. basexmpp import basexmpp
from .. xmlstream.xmlstream import XMLStream
import logging
from . import xep_0004

def stanzaPlugin(stanza, plugin):                                                                       
	stanza.plugin_attrib_map[plugin.plugin_attrib] = plugin                                             
	stanza.plugin_tag_map["{%s}%s" % (plugin.namespace, plugin.name)] = plugin 

class Pubsub(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'pubsub'
	plugin_attrib = 'pubsub'
	interfaces = set(tuple())
	plugin_attrib_map = {}
	plugin_tag_map = {}

stanzaPlugin(Iq, Pubsub)

class PubsubOwner(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	name = 'pubsub'
	plugin_attrib = 'pubsub_owner'
	interfaces = set(tuple())
	plugin_attrib_map = {}
	plugin_tag_map = {}

stanzaPlugin(Iq, PubsubOwner)

class Affiliation(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'affiliation'
	plugin_attrib = name
	interfaces = set(('node', 'affiliation'))
	plugin_attrib_map = {}
	plugin_tag_map = {}

class Affiliations(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'affiliations'
	plugin_attrib = 'affiliations'
	interfaces = set(tuple())
	plugin_attrib_map = {}
	plugin_tag_map = {}
	subitem = (Affiliation,)

	def append(self, affiliation):
		if not isinstance(affiliation, Affiliation):
			raise TypeError
		self.xml.append(affiliation.xml)
		return self.iterables.append(affiliation)

stanzaPlugin(Pubsub, Affiliations)


class Subscription(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'subscription'
	plugin_attrib = name
	interfaces = set(('jid', 'node', 'subscription', 'subid'))
	plugin_attrib_map = {}
	plugin_tag_map = {}

	def setjid(self, value):
		self._setattr('jid', str(value))
	
	def getjid(self):
		return jid(self._getattr('jid'))

stanzaPlugin(Pubsub, Subscription)

class Subscriptions(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'subscriptions'
	plugin_attrib = 'subscriptions'
	interfaces = set(tuple())
	plugin_attrib_map = {}
	plugin_tag_map = {}
	subitem = (Subscription,)

stanzaPlugin(Pubsub, Subscriptions)

class OptionalSetting(object):
	interfaces = set(('required',))

	def setRequired(self, value):
		value = bool(value)
		if value and not self['required']:
			self.xml.append(ET.Element("{%s}required" % self.namespace))
		elif not value and self['required']:
			self.delRequired()
	
	def getRequired(self):
		required = self.xml.find("{%s}required" % self.namespace)
		if required is not None:
			return True
		else:
			return False
	
	def delRequired(self):
		required = self.xml.find("{%s}required" % self.namespace)
		if required is not None:
			self.xml.remove(required)


class SubscribeOptions(ElementBase, OptionalSetting):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'subscribe-options'
	plugin_attrib = 'suboptions'
	plugin_attrib_map = {}
	plugin_tag_map = {}
	interfaces = set(('required',))

stanzaPlugin(Subscription, SubscribeOptions)

class Item(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'item'
	plugin_attrib = name
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

class Items(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'items'
	plugin_attrib = 'items'
	interfaces = set(tuple())
	plugin_attrib_map = {}
	plugin_tag_map = {}
	subitem = (Item,)

stanzaPlugin(Pubsub, Items)

class Create(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'create'
	plugin_attrib = name
	interfaces = set(('node',))
	plugin_attrib_map = {}
	plugin_tag_map = {}

stanzaPlugin(Pubsub, Create)

#class Default(ElementBase):
#	namespace = 'http://jabber.org/protocol/pubsub'
#	name = 'default'
#	plugin_attrib = name
#	interfaces = set(('node', 'type'))
#	plugin_attrib_map = {}
#	plugin_tag_map = {}
#
#	def getType(self):
#		t = self._getAttr('type')
#		if not t: t == 'leaf'
#		return t
#
#stanzaPlugin(Pubsub, Default)

class Publish(Items):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'publish'
	plugin_attrib = name
	interfaces = set(('node',))
	plugin_attrib_map = {}
	plugin_tag_map = {}
	subitem = (Item,)

stanzaPlugin(Pubsub, Publish)

class Retract(Items):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'retract'
	plugin_attrib = name
	interfaces = set(('node', 'notify'))
	plugin_attrib_map = {}
	plugin_tag_map = {}

stanzaPlugin(Pubsub, Retract)

class Unsubscribe(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'unsubscribe'
	plugin_attrib = name
	interfaces = set(('node', 'jid'))
	plugin_attrib_map = {}
	plugin_tag_map = {}
	
	def setJid(self, value):
		self._setAttr('jid', str(value))
	
	def getJid(self):
		return JID(self._getAttr('jid'))

class Subscribe(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'subscribe'
	plugin_attrib = name
	interfaces = set(('node', 'jid'))
	plugin_attrib_map = {}
	plugin_tag_map = {}

	def setJid(self, value):
		self._setAttr('jid', str(value))
	
	def getJid(self):
		return JID(self._getAttr('jid'))

stanzaPlugin(Pubsub, Subscribe)

class Configure(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'configure'
	plugin_attrib = name
	interfaces = set(('node', 'type', 'config'))
	plugin_attrib_map = {}
	plugin_tag_map = {}

	def getType(self):
		t = self._getAttr('type')
		if not t: t == 'leaf'
		return t
	
	def getConfig(self):
		config = self.xml.find('{jabber:x:data}x')
		form = xep_0004.Form()
		if config is not None:
			form.fromXML(config)
		return form
	
	def setConfig(self, value):
		self.xml.append(value.getXML())
		return self
	
	def delConfig(self):
		config = self.xml.find('{jabber:x:data}x')
		self.xml.remove(config)
	
stanzaPlugin(Pubsub, Configure)

class DefaultConfig(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	name = 'default'
	plugin_attrib = 'default'
	interfaces = set(('node', 'type', 'config'))
	plugin_attrib_map = {}
	plugin_tag_map = {}
	
	def __init__(self, *args, **kwargs):
		ElementBase.__init__(self, *args, **kwargs)
		
	def getConfig(self):
		config = self.xml.find('{jabber:x:data}x')
		form = xep_0004.Form()
		if config is not None:
			form.fromXML(config)
		return form
	
	def setConfig(self, value):
		self.xml.append(value.getXML())
		return self
	
	def delConfig(self):
		config = self.xml.find('{jabber:x:data}x')
		self.xml.remove(config)

	def getType(self):
		t = self._getAttr('type')
		if not t: t = 'leaf'
		return t

stanzaPlugin(PubsubOwner, DefaultConfig)

class Options(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'options'
	plugin_attrib = 'options'
	interfaces = set(('jid', 'node', 'options'))
	plugin_attrib_map = {}
	plugin_tag_map = {}
	
	def __init__(self, *args, **kwargs):
		ElementBase.__init__(self, *args, **kwargs)
		
	def getOptions(self):
		config = self.xml.find('{jabber:x:data}x')
		form = xep_0004.Form()
		if config is not None:
			form.fromXML(config)
		return form
	
	def setOptions(self, value):
		self.xml.append(value.getXML())
		return self
	
	def delOptions(self):
		config = self.xml.find('{jabber:x:data}x')
		self.xml.remove(config)
	
	def setJid(self, value):
		self._setAttr('jid', str(value))
	
	def getJid(self):
		return JID(self._getAttr('jid'))

stanzaPlugin(Pubsub, Options)
stanzaPlugin(Subscribe, Options)

#iq = Iq()
#iq['pubsub']['defaultconfig']
#print(iq)

#from xml.etree import cElementTree as ET
#iq = Iq()
#item = Item()
#item['payload'] = ET.Element("{http://netflint.net/p/crap}stupidshit")
#item['id'] = 'aa11bbcc'
#iq['pubsub']['items'].append(item)
#print(iq)
	
class OwnerAffiliations(Affiliations):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	interfaces = set(('node'))
	plugin_attrib_map = {}
	plugin_tag_map = {}
	
	def append(self, affiliation):
		if not isinstance(affiliation, OwnerAffiliation):
			raise TypeError
		self.xml.append(affiliation.xml)
		return self.affiliations.append(affiliation)

stanzaPlugin(PubsubOwner, OwnerAffiliations)

class OwnerAffiliation(Affiliation):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	interfaces = set(('affiliation', 'jid'))
	plugin_attrib_map = {}
	plugin_tag_map = {}

class OwnerConfigure(Configure):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	interfaces = set(('node', 'config'))
	plugin_attrib_map = {}
	plugin_tag_map = {}

stanzaPlugin(PubsubOwner, OwnerConfigure)

class OwnerDefault(OwnerConfigure):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	interfaces = set(('node', 'config'))
	plugin_attrib_map = {}
	plugin_tag_map = {}

stanzaPlugin(PubsubOwner, OwnerDefault)

class OwnerDelete(ElementBase, OptionalSetting):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	name = 'delete'
	plugin_attrib = 'delete'
	plugin_attrib_map = {}
	plugin_tag_map = {}
	interfaces = set(('node',))

stanzaPlugin(PubsubOwner, OwnerDelete)

class OwnerPurge(ElementBase, OptionalSetting):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	name = 'purge'
	plugin_attrib = name
	plugin_attrib_map = {}
	plugin_tag_map = {}

stanzaPlugin(PubsubOwner, OwnerPurge)

class OwnerRedirect(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	name = 'redirect'
	plugin_attrib = name
	interfaces = set(('node', 'jid'))
	plugin_attrib_map = {}
	plugin_tag_map = {}
	
	def setJid(self, value):
		self._setAttr('jid', str(value))
	
	def getJid(self):
		return JID(self._getAttr('jid'))

stanzaPlugin(OwnerDelete, OwnerRedirect)

class OwnerSubscriptions(Subscriptions):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	interfaces = set(('node',))
	plugin_attrib_map = {}
	plugin_tag_map = {}
	
	def append(self, subscription):
		if not isinstance(subscription, OwnerSubscription):
			raise TypeError
		self.xml.append(subscription.xml)
		return self.subscriptions.append(subscription)

stanzaPlugin(PubsubOwner, OwnerSubscriptions)

class OwnerSubscription(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	name = 'subscription'
	plugin_attrib = name
	interfaces = set(('jid', 'subscription'))
	plugin_attrib_map = {}
	plugin_tag_map = {}

	def setJid(self, value):
		self._setAttr('jid', str(value))
	
	def getJid(self):
		return JID(self._getAttr('from'))

class Event(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'event'
	plugin_attrib = 'pubsub_event'
	interfaces = set(('node',))
	plugin_attrib_map = {}
	plugin_tag_map = {}

stanzaPlugin(Message, Event)

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

stanzaPlugin(Event, EventItems)

class EventCollection(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'collection'
	plugin_attrib = name
	interfaces = set(('node',))
	plugin_attrib_map = {}
	plugin_tag_map = {}

stanzaPlugin(Event, EventCollection)

class EventAssociate(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'associate'
	plugin_attrib = name
	interfaces = set(('node',))
	plugin_attrib_map = {}
	plugin_tag_map = {}

stanzaPlugin(EventCollection, EventAssociate)

class EventDisassociate(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'disassociate'
	plugin_attrib = name
	interfaces = set(('node',))
	plugin_attrib_map = {}
	plugin_tag_map = {}

stanzaPlugin(EventCollection, EventDisassociate)

class EventConfiguration(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'configuration'
	plugin_attrib = name
	interfaces = set(('node', 'config'))
	plugin_attrib_map = {}
	plugin_tag_map = {}
	
	def getConfig(self):
		config = self.xml.find('{jabber:x:data}x')
		form = xep_0004.Form()
		if config is not None:
			form.fromXML(config)
		return form
	
	def setConfig(self, value):
		self.xml.append(value.getXML())
		return self
	
	def delConfig(self):
		config = self.xml.find('{jabber:x:data}x')
		self.xml.remove(config)
	
stanzaPlugin(Event, EventConfiguration)

class EventPurge(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#event'
	name = 'purge'
	plugin_attrib = name
	interfaces = set(('node',))
	plugin_attrib_map = {}
	plugin_tag_map = {}

stanzaPlugin(Event, EventPurge)

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

stanzaPlugin(Event, EventSubscription)
