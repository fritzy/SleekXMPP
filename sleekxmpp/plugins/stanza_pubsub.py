from .. xmlstream.stanzabase import ElementBase, ET
from .. stanza.iq import Iq
from .. basexmpp import basexmpp
from .. xmlstream.xmlstream import XMLStream
from . import xep_0004


def stanzaPlugin(stanza, plugin):                                                                       
    stanza.plugin_attrib_map[plugin.plugin_attrib] = plugin                                             
    stanza.plugin_tag_map["{%s}%s" % (plugin.namespace, plugin.name)] = plugin 

class Pubsub(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'pubsub'
	plugin_attrib = 'pubsub'
	interfaces = set((
		'create',
		'configure',
		'subscribe',
		'options',
		'default',
		'items',
		'publish',
		'retract',
		'subscription',
		'subscriptions',
		'unsubscribe',
	))

stanzaPlugin(Iq, Pubsub)

class Affiliations(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'affiliations'
	plugin_attrib = 'affiliations'
	interfaces = set(tuple())

	def __init__(self, *args, **kwargs):
		ElementBase.__init__(self, *args, **kwargs)
		self.affiliations = []
		self.idx = 0

	def __iter__(self):
		self.idx = 0
		return self
	
	def __next__(self):
		self.idx += 1
		if self.idx + 1 > len(self.affilations):
			self.idx = 0
			raise StopIteration
		return self.affiliations[self.idx]
	
	def __len__(self):
		return len(self.affiliations)
	
	def append(self, affiliation):
		if not isinstance(affiliation, Affiliation):
			raise TypeError
		self.xml.append(affiliation.xml)
		return self.affiliations.append(affiliation)
	
	def pop(self, idx=0):
		aff = self.affiliations.pop(idx)
		self.xml.remove(aff.xml)
		return aff
	
	def find(self, affilation):
		return self.affilations.find(affiliation)

stanzaPlugin(Pubsub, Affiliations)

class Affiliation(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'affiliation'
	plugin_attrib = name
	interfaces = set(('node', 'affiliation'))

class Items(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'items'
	plugin_attrib = 'items'
	interfaces = set(tuple())

	def __init__(self, *args, **kwargs):
		ElementBase.__init__(self, *args, **kwargs)
		self.items = []
		self.idx = 0

	def __iter__(self):
		self.idx = 0
		return self
	
	def __next__(self):
		self.idx += 1
		if self.idx + 1 > len(self.items):
			self.idx = 0
			raise StopIteration
		return self.items[self.idx]
	
	def __len__(self):
		return len(self.items)
	
	def append(self, item):
		if not isinstance(item, Item):
			raise TypeError
		self.xml.append(item.xml)
		return self.items.append(item)
	
	def pop(self, idx=0):
		aff = self.items.pop(idx)
		self.xml.remove(aff.xml)
		return aff
	
	def find(self, item):
		return self.items.find(item)

stanzaPlugin(Pubsub, Items)

class Item(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'affiliation'
	plugin_attrib = name
	interfaces = set(('node', 'affiliation'))
class DefaultConfig(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'default'
	plugin_attrib = 'defaultconfig'
	interfaces = set(('node', 'type', 'config'))
	
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

stanzaPlugin(Pubsub, DefaultConfig)

iq = Iq()
aff1 = Affiliation()
aff1['node'] = 'testnode'
aff1['affiliation'] = 'owner'
aff2 = Affiliation()
aff2['node'] = 'testnode2'
aff2['affiliation'] = 'publisher'
iq['pubsub']['affiliations'].append(aff1)
iq['pubsub']['affiliations'].append(aff2)
print(iq)
iq['pubsub']['affiliations'].pop(0)
print(iq)

iq = Iq()
iq['pubsub']['defaultconfig']
print(iq)
	
class OwnerAffiliations(Affiliations):
	pass

class OwnerAffiation(Affiliation):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	interfaces = set(('node', 'affiliation', 'jid'))

class PubSubOwner(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	nick = 'pubsubowner'
