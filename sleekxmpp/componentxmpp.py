#!/usr/bin/python2.6

"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
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

	def __init__(self, jid, secret, host, port, plugin_config = {}, plugin_whitelist=[], use_jc_ns=False):
		XMLStream.__init__(self)
		if use_jc_ns:
			self.default_ns = 'jabber:client'
		else:
			self.default_ns = 'jabber:component:accept'
		basexmpp.__init__(self)
		self.auto_authorize = None
		self.stream_header = "<stream:stream xmlns='jabber:component:accept' xmlns:stream='http://etherx.jabber.org/streams' to='%s'>" % jid
		self.stream_footer = "</stream:stream>"
		self.server_host = host
		self.server_port = port
		self.set_jid(jid)
		self.secret = secret
		self.registerHandler(Callback('Handshake', MatchXPath('{jabber:component:accept}handshake'), self._handleHandshake))
	
	def __getitem__(self, key):
		if key in self.plugin:
			return self.plugin[key]
		else:
			logging.warning("""Plugin "%s" is not loaded.""" % key)
			return False
	
	def get(self, key, default):
		return self.plugin.get(key, default)
	
	def incoming_filter(self, xmlobj):
		if xmlobj.tag.startswith('{jabber:client}'):
			xmlobj.tag = xmlobj.tag.replace('jabber:client', self.default_ns)
		for sub in xmlobj:
			self.incoming_filter(sub)
		return xmlobj

	def start_stream_handler(self, xml):
		sid = xml.get('id', '')
		handshake = ET.Element('{jabber:component:accept}handshake')
		if sys.version_info < (3,0):
			handshake.text = hashlib.sha1("%s%s" % (sid, self.secret)).hexdigest().lower()
		else:
			handshake.text = hashlib.sha1(bytes("%s%s" % (sid, self.secret), 'utf-8')).hexdigest().lower()
		self.sendXML(handshake)
	
	def _handleHandshake(self, xml):
		self.event("session_start")
	
	def connect(self):
		logging.debug("Connecting to %s:%s" % (self.server_host, self.server_port))
		return xmlstreammod.XMLStream.connect(self, self.server_host, self.server_port)
