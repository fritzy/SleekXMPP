#!/usr/bin/python2.5

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
from __future__ import absolute_import
from . basexmpp import basexmpp
from xml.etree import cElementTree as ET

from . xmlstream.xmlstream import XMLStream
from . xmlstream.xmlstream import RestartStream
from . xmlstream.matcher.xmlmask import MatchXMLMask
from . xmlstream.matcher.xpath import MatchXPath
from . xmlstream.matcher.many import MatchMany
from . xmlstream.handler.callback import Callback
from . xmlstream.stanzabase import StanzaBase
from . xmlstream import xmlstream as xmlstreammod
import time
import logging
import base64
import sys
import random
import copy
from . import plugins
from . import stanza
import hashlib
srvsupport = True
try:
	import dns.resolver
except ImportError:
	srvsupport = False


class ComponentXMPP(basexmpp, XMLStream):
	"""SleekXMPP's client class.  Use only for good, not evil."""

	def __init__(self, jid, secret, host, port, plugin_config = {}, plugin_whitelist=[]):
		XMLStream.__init__(self)
		self.default_ns = 'jabber:component:accept'
		basexmpp.__init__(self)
		self.auto_authorize = None
		self.stream_header = "<stream:stream xmlns='jabber:component:accept' xmlns:stream='http://etherx.jabber.org/streams' to='%s'>" % jid
		self.stream_footer = "</stream:stream>"
		self.server_host = host
		self.server_port = port
		self.set_jid(jid)
		self.secret = secret
		self.registerHandler(Callback('PresenceProbe', MatchXMLMask("<presence xmlns='%s' type='probe'/>" % self.default_ns), self._handlePresenceProbe))
		self.registerHandler(Callback('Handshake', MatchXPath('{jabber:component:accept}handshake'), self._handleHandshake))
		self.registerHandler(Callback('PresenceSubscription', MatchMany(\
			(MatchXMLMask("<presence xmlns='%s' type='subscribe'/>" % self.default_ns), \
			 MatchXMLMask("<presence xmlns='%s' type='subscribed'/>" % self.default_ns), \
			 MatchXMLMask("<presence xmlns='%s' type='unsubscribe'/>" % self.default_ns), \
			 MatchXMLMask("<presence xmlns='%s' type='unsubscribed'/>" % self.default_ns) \
			 )), self._handlePresenceSubscription))
	
	def incoming_filter(self, xmlobj):
		if xmlobj.tag.startswith('{jabber:client}'):
			xmlobj.tag = xmlobj.tag.replace('jabber:client', 'jabber:component:accept')
			for child in xmlobj.getchildren():
				child = self.incoming_filter(child)
		return xmlobj


	def _handlePresenceProbe(self, stanza):
		xml = stanza.xml
		self.event("got_presence_probe", ({
				'from': xml.attrib['from'],
				'to': xml.attrib['to']
			}))

	def _handlePresenceSubscription(self, presence):
		xml = presence.xml
		self.event("changed_subscription", {
				'type' : xml.attrib['type'],
				'from': xml.attrib['from'],
				'to': xml.attrib['to'] 
			})
	
	def start_stream_handler(self, xml):
		sid = xml.get('id', '')
		handshake = ET.Element('{jabber:component:accept}handshake')
		handshake.text = hashlib.sha1.new(b"%s%s" % (sid, self.secret)).hexdigest().lower()
		self.send(handshake)
	
	def _handleHandshake(self, xml):
		self.event("session_start")
	
	def connect(self):
		logging.debug("Connecting to %s:%s" % (self.server_host, self.server_port))
		return xmlstreammod.XMLStream.connect(self, self.server_host, self.server_port)
