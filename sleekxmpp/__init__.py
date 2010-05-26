#!/usr/bin/python2.5

"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from __future__ import absolute_import, unicode_literals
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
from . stanza.message import Message
from . stanza.iq import Iq
import time
import logging
import base64
import sys
import random
import copy
from . import plugins
#from . import stanza
srvsupport = True
try:
	import dns.resolver
except ImportError:
	srvsupport = False



#class PresenceStanzaType(object):
#	
#	def fromXML(self, xml):
#		self.ptype = xml.get('type')


class ClientXMPP(basexmpp, XMLStream):
	"""SleekXMPP's client class.  Use only for good, not evil."""

	def __init__(self, jid, password, ssl=False, plugin_config = {}, plugin_whitelist=[], escape_quotes=True):
		global srvsupport
		XMLStream.__init__(self)
		self.default_ns = 'jabber:client'
		basexmpp.__init__(self)
		self.plugin_config = plugin_config
		self.escape_quotes = escape_quotes
		self.set_jid(jid)
		self.plugin_whitelist = plugin_whitelist
		self.auto_reconnect = True
		self.srvsupport = srvsupport
		self.password = password
		self.registered_features = []
		self.stream_header = """<stream:stream to='%s' xmlns:stream='http://etherx.jabber.org/streams' xmlns='%s' version='1.0'>""" % (self.server,self.default_ns)
		self.stream_footer = "</stream:stream>"
		#self.map_namespace('http://etherx.jabber.org/streams', 'stream')
		#self.map_namespace('jabber:client', '')
		self.features = []
		#TODO: Use stream state here
		self.authenticated = False
		self.sessionstarted = False
		self.registerHandler(Callback('Stream Features', MatchXPath('{http://etherx.jabber.org/streams}features'), self._handleStreamFeatures, thread=True))
		self.registerHandler(Callback('Roster Update', MatchXPath('{%s}iq/{jabber:iq:roster}query' % self.default_ns), self._handleRoster, thread=True))
		#self.registerHandler(Callback('Roster Update', MatchXMLMask("<presence xmlns='%s' type='subscribe' />" % self.default_ns), self._handlePresenceSubscribe, thread=True))
		self.registerFeature("<starttls xmlns='urn:ietf:params:xml:ns:xmpp-tls' />", self.handler_starttls, True)
		self.registerFeature("<mechanisms xmlns='urn:ietf:params:xml:ns:xmpp-sasl' />", self.handler_sasl_auth, True)
		self.registerFeature("<bind xmlns='urn:ietf:params:xml:ns:xmpp-bind' />", self.handler_bind_resource)
		self.registerFeature("<session xmlns='urn:ietf:params:xml:ns:xmpp-session' />", self.handler_start_session)
		
		#self.registerStanzaExtension('PresenceStanza', PresenceStanzaType)
		#self.register_plugins()
	
	def __getitem__(self, key):
		if key in self.plugin:
			return self.plugin[key]
		else:
			logging.warning("""Plugin "%s" is not loaded.""" % key)
			return False
	
	def get(self, key, default):
		return self.plugin.get(key, default)

	def connect(self, address=tuple()):
		"""Connect to the Jabber Server.  Attempts SRV lookup, and if it fails, uses
		the JID server."""
		if not address or len(address) < 2:
			if not self.srvsupport:
				logging.debug("Did not supply (address, port) to connect to and no SRV support is installed (http://www.dnspython.org).  Continuing to attempt connection, using server hostname from JID.")
			else:
				logging.debug("Since no address is supplied, attempting SRV lookup.")
				try:
					answers = dns.resolver.query("_xmpp-client._tcp.%s" % self.server, dns.rdatatype.SRV)
				except dns.resolver.NXDOMAIN:
					logging.debug("No appropriate SRV record found.  Using JID server name.")
				else:
					# pick a random answer, weighted by priority
					# there are less verbose ways of doing this (random.choice() with answer * priority), but I chose this way anyway 
					# suggestions are welcome
					addresses = {}
					intmax = 0
					priorities = []
					for answer in answers:
						intmax += answer.priority
						addresses[intmax] = (answer.target.to_text()[:-1], answer.port)
						priorities.append(intmax) # sure, I could just do priorities = addresses.keys()\n priorities.sort()
					picked = random.randint(0, intmax)
					for priority in priorities:
						if picked <= priority:
							address = addresses[priority]
							break
		if not address:
			# if all else fails take server from JID.
			address = (self.server, 5222)
		result = XMLStream.connect(self, address[0], address[1], use_tls=True)
		if result:
			self.event("connected")
		else:
			logging.warning("Failed to connect")
			self.event("disconnected")
		return result
	
	# overriding reconnect and disconnect so that we can get some events
	# should events be part of or required by xmlstream?  Maybe that would be cleaner
	def reconnect(self):
		logging.info("Reconnecting")
		self.event("disconnected")
		XMLStream.reconnect(self)
	
	def disconnect(self, init=True, close=False, reconnect=False):
		self.event("disconnected")
		XMLStream.disconnect(self, reconnect)
	
	def registerFeature(self, mask, pointer, breaker = False):
		"""Register a stream feature."""
		self.registered_features.append((MatchXMLMask(mask), pointer, breaker))

	def updateRoster(self, jid, name=None, subscription=None, groups=[]):
		"""Add or change a roster item."""
		iq = self.Iq().setValues({'type': 'set'})
		iq['roster'] = {jid: {'name': name, 'subscription': subscription, 'groups': groups}}
		#self.send(iq, self.Iq().setValues({'id': iq['id']}))
		r = iq.send()
		return r['type'] == 'result'
	
	def getRoster(self):
		"""Request the roster be sent."""
		iq = self.Iq().setValues({'type': 'get'}).enable('roster').send()
		self._handleRoster(iq, request=True)
	
	def _handleStreamFeatures(self, features):
		self.features = []
		for sub in features.xml:
			self.features.append(sub.tag)
		for subelement in features.xml:
			for feature in self.registered_features:
				if feature[0].match(subelement):
				#if self.maskcmp(subelement, feature[0], True):
					if feature[1](subelement) and feature[2]: #if breaker, don't continue
						return True
	
	def handler_starttls(self, xml):
		if not self.authenticated and self.ssl_support:
			self.add_handler("<proceed xmlns='urn:ietf:params:xml:ns:xmpp-tls' />", self.handler_tls_start, instream=True)
			self.sendXML(xml)
			return True
		else:
			logging.warning("The module tlslite is required in to some servers, and has not been found.")
			return False

	def handler_tls_start(self, xml):
		logging.debug("Starting TLS")
		if self.startTLS():
			raise RestartStream()
	
	def handler_sasl_auth(self, xml):
		if '{urn:ietf:params:xml:ns:xmpp-tls}starttls' in self.features:
			return False
		logging.debug("Starting SASL Auth")
		self.add_handler("<success xmlns='urn:ietf:params:xml:ns:xmpp-sasl' />", self.handler_auth_success, instream=True)
		self.add_handler("<failure xmlns='urn:ietf:params:xml:ns:xmpp-sasl' />", self.handler_auth_fail, instream=True)
		sasl_mechs = xml.findall('{urn:ietf:params:xml:ns:xmpp-sasl}mechanism')
		if len(sasl_mechs):
			for sasl_mech in sasl_mechs:
				self.features.append("sasl:%s" % sasl_mech.text)
			if 'sasl:PLAIN' in self.features:
				if sys.version_info < (3,0):
					self.send("""<auth xmlns='urn:ietf:params:xml:ns:xmpp-sasl' mechanism='PLAIN'>%s</auth>""" % base64.b64encode(b'\x00' + bytes(self.username) + b'\x00' + bytes(self.password)).decode('utf-8'))
				else:
					self.send("""<auth xmlns='urn:ietf:params:xml:ns:xmpp-sasl' mechanism='PLAIN'>%s</auth>""" % base64.b64encode(b'\x00' + bytes(self.username, 'utf-8') + b'\x00' + bytes(self.password, 'utf-8')).decode('utf-8'))
			else:
				logging.error("No appropriate login method.")
				self.disconnect()
				#if 'sasl:DIGEST-MD5' in self.features:
				#	self._auth_digestmd5()
		return True
	
	def handler_auth_success(self, xml):
		self.authenticated = True
		self.features = []
		raise RestartStream()

	def handler_auth_fail(self, xml):
		logging.info("Authentication failed.")
		self.disconnect()
		self.event("failed_auth")
	
	def handler_bind_resource(self, xml):
		logging.debug("Requesting resource: %s" % self.resource)
		iq = self.Iq(stype='set')
		res = ET.Element('resource')
		res.text = self.resource
		xml.append(res)
		iq.append(xml)
		response = iq.send()
		#response = self.send(iq, self.Iq(sid=iq['id']))
		self.set_jid(response.xml.find('{urn:ietf:params:xml:ns:xmpp-bind}bind/{urn:ietf:params:xml:ns:xmpp-bind}jid').text)
		logging.info("Node set to: %s" % self.fulljid)
		if "{urn:ietf:params:xml:ns:xmpp-session}session" not in self.features:
			logging.debug("Established Session")
			self.sessionstarted = True
			self.event("session_start")
	
	def handler_start_session(self, xml):
		if self.authenticated:
			iq = self.makeIqSet(xml)
			response = iq.send()
			logging.debug("Established Session")
			self.sessionstarted = True
			self.event("session_start")
	
	def _handleRoster(self, iq, request=False):
		if iq['type'] == 'set' or (iq['type'] == 'result' and request):
			for jid in iq['roster']['items']:
				if not jid in self.roster:
					self.roster[jid] = {'groups': [], 'name': '', 'subscription': 'none', 'presence': {}, 'in_roster': True}
				self.roster[jid].update(iq['roster']['items'][jid])
			if iq['type'] == 'set':
				self.send(self.Iq().setValues({'type': 'result', 'id': iq['id']}).enable('roster'))
		self.event("roster_update", iq)
