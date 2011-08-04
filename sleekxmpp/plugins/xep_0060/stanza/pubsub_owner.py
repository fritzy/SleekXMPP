from sleekxmpp.xmlstream.stanzabase import registerStanzaPlugin, ElementBase, ET, JID
from sleekxmpp.stanza.iq import Iq
from sleekxmpp.stanza.message import Message
from sleekxmpp.basexmpp import basexmpp
from sleekxmpp.xmlstream.xmlstream import XMLStream
import logging
from sleekxmpp.plugins import xep_0004
from base import OptionalSetting
from pubsub import Affiliations, Affiliation, Configure, Subscriptions

class PubsubOwner(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	name = 'pubsub'
	plugin_attrib = 'pubsub_owner'
	interfaces = set(tuple())
	plugin_attrib_map = {}
	plugin_tag_map = {}

registerStanzaPlugin(Iq, PubsubOwner)

class DefaultConfig(ElementBase):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	name = 'default'
	plugin_attrib = 'default'
	interfaces = set(('node', 'type', 'config'))
	plugin_attrib_map = {}
	plugin_tag_map = {}
	
	def __init__(self, *args, **kwargs):
		ElementBase.__init__(self, *args, **kwargs)

	def getType(self):
		t = self._getAttr('type')
		if not t: t = 'leaf'
		return t
	
	def getConfig(self):
		return self['form']
	
	def setConfig(self, value):
		self['form'].setStanzaValues(value.getStanzaValues())
		return self

registerStanzaPlugin(PubsubOwner, DefaultConfig)
registerStanzaPlugin(DefaultConfig, xep_0004.Form)

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

registerStanzaPlugin(PubsubOwner, OwnerAffiliations)

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

registerStanzaPlugin(PubsubOwner, OwnerConfigure)

class OwnerDefault(OwnerConfigure):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	interfaces = set(('node', 'config'))
	plugin_attrib_map = {}
	plugin_tag_map = {}
	
	def getConfig(self):
		return self['form']
	
	def setConfig(self, value):
		self['form'].setStanzaValues(value.getStanzaValues())
		return self

registerStanzaPlugin(PubsubOwner, OwnerDefault)
registerStanzaPlugin(OwnerDefault, xep_0004.Form)

class OwnerDelete(ElementBase, OptionalSetting):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	name = 'delete'
	plugin_attrib = 'delete'
	plugin_attrib_map = {}
	plugin_tag_map = {}
	interfaces = set(('node',))

registerStanzaPlugin(PubsubOwner, OwnerDelete)

class OwnerPurge(ElementBase, OptionalSetting):
	namespace = 'http://jabber.org/protocol/pubsub#owner'
	name = 'purge'
	plugin_attrib = name
	plugin_attrib_map = {}
	plugin_tag_map = {}

registerStanzaPlugin(PubsubOwner, OwnerPurge)

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

registerStanzaPlugin(OwnerDelete, OwnerRedirect)

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

registerStanzaPlugin(PubsubOwner, OwnerSubscriptions)

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
