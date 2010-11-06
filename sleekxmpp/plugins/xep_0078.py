"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""
from __future__ import with_statement
from xml.etree import cElementTree as ET
import logging
import hashlib
from . import base


log = logging.getLogger(__name__)


class xep_0078(base.base_plugin):
	"""
	XEP-0078 NON-SASL Authentication
	"""
	def plugin_init(self):
		self.description = "Non-SASL Authentication (broken)"
		self.xep = "0078"
		self.xmpp.add_event_handler("session_start", self.check_stream)
		#disabling until I fix conflict with PLAIN
		#self.xmpp.registerFeature("<auth xmlns='http://jabber.org/features/iq-auth'/>", self.auth)
		self.streamid = ''

	def check_stream(self, xml):
		self.streamid = xml.attrib['id']
		if xml.get('version', '0') != '1.0':
			self.auth()

	def auth(self, xml=None):
		log.debug("Starting jabber:iq:auth Authentication")
		auth_request = self.xmpp.makeIqGet()
		auth_request_query = ET.Element('{jabber:iq:auth}query')
		auth_request.attrib['to'] = self.xmpp.server
		username = ET.Element('username')
		username.text = self.xmpp.username
		auth_request_query.append(username)
		auth_request.append(auth_request_query)
		result = auth_request.send()
		rquery = result.find('{jabber:iq:auth}query')
		attempt = self.xmpp.makeIqSet()
		query = ET.Element('{jabber:iq:auth}query')
		resource = ET.Element('resource')
		resource.text = self.xmpp.resource
		query.append(username)
		query.append(resource)
		if rquery.find('{jabber:iq:auth}digest') is None:
			log.warning("Authenticating via jabber:iq:auth Plain.")
			password = ET.Element('password')
			password.text = self.xmpp.password
			query.append(password)
		else:
			log.debug("Authenticating via jabber:iq:auth Digest")
			digest = ET.Element('digest')
			digest.text = hashlib.sha1(b"%s%s" % (self.streamid, self.xmpp.password)).hexdigest()
			query.append(digest)
		attempt.append(query)
		result = attempt.send()
		if result.attrib['type'] == 'result':
			with self.xmpp.lock:
				self.xmpp.authenticated = True
				self.xmpp.sessionstarted = True
			self.xmpp.event("session_start")
		else:
			log.info("Authentication failed")
			self.xmpp.disconnect()
			self.xmpp.event("failed_auth")
