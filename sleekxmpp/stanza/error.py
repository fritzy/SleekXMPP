"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from .. xmlstream.stanzabase import ElementBase, ET

class Error(ElementBase):
	namespace = 'jabber:client'
	name = 'error'
	plugin_attrib = 'error'
	conditions = set(('bad-request', 'conflict', 'feature-not-implemented', 'forbidden', 'gone', 'item-not-found', 'jid-malformed', 'not-acceptable', 'not-allowed', 'not-authorized', 'payment-required', 'recipient-unavailable', 'redirect', 'registration-required', 'remote-server-not-found', 'remote-server-timeout', 'service-unavailable', 'subscription-required', 'undefined-condition', 'unexpected-request'))
	interfaces = set(('condition', 'text', 'type'))
	types = set(('cancel', 'continue', 'modify', 'auth', 'wait'))
	sub_interfaces = set(('text',))
	condition_ns = 'urn:ietf:params:xml:ns:xmpp-stanzas'
	
	def setup(self, xml=None):
		if ElementBase.setup(self, xml): #if we had to generate xml
			self['type'] = 'cancel'
			self['condition'] = 'feature-not-implemented'
		if self.parent is not None:
			self.parent['type'] = 'error'
	
	def getCondition(self):
		for child in self.xml.getchildren():
			if "{%s}" % self.condition_ns in child.tag:
				return child.tag.split('}', 1)[-1]
		return ''
	
	def setCondition(self, value):
		if value in self.conditions:
			for child in self.xml.getchildren():
				if "{%s}" % self.condition_ns in child.tag:
					self.xml.remove(child)
			condition = ET.Element("{%s}%s" % (self.condition_ns, value))
			self.xml.append(condition)
		return self
	
	def delCondition(self):
		return self
	
	def getText(self):
		text = ''
		textxml = self.xml.find("{urn:ietf:params:xml:ns:xmpp-stanzas}text")
		if textxml is not None:
			text = textxml.text
		return text
	
	def setText(self, value):
		self.delText()
		textxml = ET.Element('{urn:ietf:params:xml:ns:xmpp-stanzas}text')
		textxml.text = value
		self.xml.append(textxml)
		return self
	
	def delText(self):
		textxml = self.xml.find("{urn:ietf:params:xml:ns:xmpp-stanzas}text")
		if textxml is not None:
			self.xml.remove(textxml)
