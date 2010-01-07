from .. xmlstream.stanzabase import ElementBase, ET, JID
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
	interfaces = set(tuple())

stanzaPlugin(Iq, Pubsub)

class PubsubOwner(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	name = 'pubsub_owner'
	plugin_attrib = 'pubsub'
	interfaces = set(tuple())

stanzaPlugin(Iq, PubsubOwner)

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
		if self.idx + 1 > len(self.affiliations):
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
	
	def find(self, affiliation):
		return self.affiliations.find(affiliation)

stanzaPlugin(Pubsub, Affiliations)

class Subscriptions(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'subscriptions'
	plugin_attrib = 'subscriptions'
	interfaces = set(tuple())

	def __init__(self, *args, **kwargs):
		ElementBase.__init__(self, *args, **kwargs)
		self.subscriptions = []
		self.idx = 0

	def __iter__(self):
		self.idx = 0
		return self
	
	def __next__(self):
		self.idx += 1
		if self.idx + 1 > len(self.subscriptions):
			self.idx = 0
			raise StopIteration
		return self.subscriptions[self.idx]
	
	def __len__(self):
		return len(self.subscriptions)
	
	def append(self, subscription):
		if not isinstance(subscription, Subscription):
			raise TypeError
		self.xml.append(subscription.xml)
		return self.subscriptions.append(subscription)
	
	def pop(self, idx=0):
		aff = self.subscriptions.pop(idx)
		self.xml.remove(aff.xml)
		return aff
	
	def find(self, subscription):
		return self.subscriptions.find(subscription)

stanzaPlugin(Pubsub, Subscriptions)

class Affiliation(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'affiliation'
	plugin_attrib = name
	interfaces = set(('node', 'affiliation'))

class Subscription(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'subscription'
	plugin_attrib = name
	interfaces = set(('jid', 'node', 'subid', 'subscription'))

	def setJid(self, value):
		self._setAttr('jid', str(value))
	
	def getJid(self):
		return JID(self._getAttr('from'))

stanzaPlugin(Pubsub, Subscription)

class OptionalSetting(object):
	interfaces = set(('required'))

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
	plugin_attrib = 'options'

stanzaPlugin(Subscription, SubscribeOptions)

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
	name = 'item'
	plugin_attrib = name
	interfaces = set(('id', 'payload'))

	def setPayload(self, value):
		self.xml.append(value)
	
	def getPayload(self):
		childs = self.xml.getchildren()
		if len(childs) > 0:
			return childs[0]
	
	def delPayload(self):
		for child in self.xml.getchildren():
			self.xml.remove(child)

class Create(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'create'
	plugin_attrib = name
	interfaces = set(('node'))

stanzaPlugin(Pubsub, Create)

class Default(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'default'
	plugin_attrib = name
	interfaces = set(('node', 'type'))

	def getType(self):
		t = self._getAttr('type')
		if not t: t == 'leaf'
		return t

stanzaPlugin(Pubsub, Default)

class Publish(Items):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'publish'
	plugin_attrib = name
	interfaces = set(('node'))

stanzaPlugin(Pubsub, Publish)

class Retract(Items):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'retract'
	plugin_attrib = name
	interfaces = set(('node', 'notify'))

stanzaPlugin(Pubsub, Retract)

class Unsubscribe(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'unsubscribe'
	plugin_attrib = name
	interfaces = set(('node', 'jid'))
	
	def setJid(self, value):
		self._setAttr('jid', str(value))
	
	def getJid(self):
		return JID(self._getAttr('from'))

class Subscribe(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'subscribe'
	plugin_attrib = name
	interfaces = set(('node', 'jid'))

	def setJid(self, value):
		self._setAttr('jid', str(value))
	
	def getJid(self):
		return JID(self._getAttr('from'))

stanzaPlugin(Pubsub, Subscribe)

class Configure(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'configure'
	plugin_attrib = name
	interfaces = set(('node', 'type', 'config'))

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

class Options(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub'
	name = 'options'
	plugin_attrib = 'options'
	interfaces = set(('jid', 'node', 'options'))
	
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
		return JID(self._getAttr('from'))

stanzaPlugin(Pubsub, Options)

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

from xml.etree import cElementTree as ET
iq = Iq()
item = Item()
item['payload'] = ET.Element("{http://netflint.net/p/crap}stupidshit")
item['id'] = 'aa11bbcc'
iq['pubsub']['items'].append(item)
print(iq)
	
class OwnerAffiliations(Affiliations):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	interfaces = set(('node'))
	
	def append(self, affiliation):
		if not isinstance(affiliation, OwnerAffiliation):
			raise TypeError
		self.xml.append(affiliation.xml)
		return self.affiliations.append(affiliation)

stanzaPlugin(PubsubOwner, OwnerAffiliations)

class OwnerAffiliation(Affiliation):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	interfaces = set(('affiliation', 'jid'))

class OwnerConfigure(Configure):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	interfaces = set(('node', 'config'))

stanzaPlugin(PubsubOwner, OwnerConfigure)

class OwnerDefault(OwnerConfigure):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	interfaces = set(('node', 'config'))

stanzaPlugin(PubsubOwner, OwnerDefault)

class OwnerDelete(ElementBase, OptionalSetting):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	name = 'delete'
	plugin_attrib = 'delete'

stanzaPlugin(PubsubOwner, OwnerDelete)

class OwnerPurge(ElementBase, OptionalSetting):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	name = 'purge'
	plugin_attrib = name

stanzaPlugin(PubsubOwner, OwnerPurge)

class OwnerRedirect(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	name = 'redirect'
	plugin_attrib = name
	interfaces = set(('node', 'jid'))
	
	def setJid(self, value):
		self._setAttr('jid', str(value))
	
	def getJid(self):
		return JID(self._getAttr('from'))

stanzaPlugin(OwnerDelete, OwnerRedirect)

class OwnerSubscriptions(Subscriptions):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	interfaces = set(('node',))
	
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

	def setJid(self, value):
		self._setAttr('jid', str(value))
	
	def getJid(self):
		return JID(self._getAttr('from'))
