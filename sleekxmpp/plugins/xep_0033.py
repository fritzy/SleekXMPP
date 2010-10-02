"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging
from . import base
from .. xmlstream.handler.callback import Callback
from .. xmlstream.matcher.xpath import MatchXPath
from .. xmlstream.stanzabase import registerStanzaPlugin, ElementBase, ET, JID
from .. stanza.message import Message


class Addresses(ElementBase):
	namespace = 'http://jabber.org/protocol/address'
	name = 'addresses'
	plugin_attrib = 'addresses'
	interfaces = set(('addresses', 'bcc', 'cc', 'noreply', 'replyroom', 'replyto', 'to'))

	def addAddress(self, atype='to', jid='', node='', uri='', desc='', delivered=False):
		address = Address(parent=self)
		address['type'] = atype
		address['jid'] = jid
		address['node'] = node
		address['uri'] = uri
		address['desc'] = desc
		address['delivered'] = delivered
		return address

	def getAddresses(self, atype=None):
		addresses = []
		for addrXML in self.xml.findall('{%s}address' % Address.namespace):
			# ElementTree 1.2.6 does not support [@attr='value'] in findall
			if atype is None or addrXML.attrib.get('type') == atype:
				addresses.append(Address(xml=addrXML, parent=None))
		return addresses

	def setAddresses(self, addresses, set_type=None):
		self.delAddresses(set_type)
		for addr in addresses:
			addr = dict(addr)
			# Remap 'type' to 'atype' to match the add method
			if set_type is not None:
				addr['type'] = set_type
			curr_type = addr.get('type', None)
			if curr_type is not None:
				del addr['type']
				addr['atype'] = curr_type
			self.addAddress(**addr)

	def delAddresses(self, atype=None):
		if atype is None:
			return
		for addrXML in self.xml.findall('{%s}address' % Address.namespace):
			# ElementTree 1.2.6 does not support [@attr='value'] in findall
			if addrXML.attrib.get('type') == atype:
				self.xml.remove(addrXML)

	# --------------------------------------------------------------

	def delBcc(self):
		self.delAddresses('bcc')

	def delCc(self):
		self.delAddresses('cc')

	def delNoreply(self):
		self.delAddresses('noreply')

	def delReplyroom(self):
		self.delAddresses('replyroom')

	def delReplyto(self):
		self.delAddresses('replyto')

	def delTo(self):
		self.delAddresses('to')

	# --------------------------------------------------------------

	def getBcc(self):
		return self.getAddresses('bcc')

	def getCc(self):
		return self.getAddresses('cc')

	def getNoreply(self):
		return self.getAddresses('noreply')

	def getReplyroom(self):
		return self.getAddresses('replyroom')

	def getReplyto(self):
		return self.getAddresses('replyto')

	def getTo(self):
		return self.getAddresses('to')

	# --------------------------------------------------------------

	def setBcc(self, addresses):
		self.setAddresses(addresses, 'bcc')

	def setCc(self, addresses):
		self.setAddresses(addresses, 'cc')

	def setNoreply(self, addresses):
		self.setAddresses(addresses, 'noreply')

	def setReplyroom(self, addresses):
		self.setAddresses(addresses, 'replyroom')

	def setReplyto(self, addresses):
		self.setAddresses(addresses, 'replyto')

	def setTo(self, addresses):
		self.setAddresses(addresses, 'to')


class Address(ElementBase):
	namespace = 'http://jabber.org/protocol/address'
	name = 'address'
	plugin_attrib = 'address'
	interfaces = set(('delivered', 'desc', 'jid', 'node', 'type', 'uri'))
	address_types = set(('bcc', 'cc', 'noreply', 'replyroom', 'replyto', 'to'))

	def getDelivered(self):
		return self.xml.attrib.get('delivered', False)

	def setDelivered(self, delivered):
		if delivered:
			self.xml.attrib['delivered'] = "true"
		else:
			del self['delivered']

	def setUri(self, uri):
		if uri:
			del self['jid']
			del self['node']
			self.xml.attrib['uri'] = uri
		elif 'uri' in self.xml.attrib:
			del self.xml.attrib['uri']


class xep_0033(base.base_plugin):
	"""
	XEP-0033: Extended Stanza Addressing
	"""

	def plugin_init(self):
		self.xep = '0033'
		self.description = 'Extended Stanza Addressing'

		registerStanzaPlugin(Message, Addresses)

	def post_init(self):
		base.base_plugin.post_init(self)
		self.xmpp.plugin['xep_0030'].add_feature(Addresses.namespace)
