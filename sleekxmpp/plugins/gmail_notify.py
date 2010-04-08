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
from __future__ import with_statement
from . import base
import logging
from xml.etree import cElementTree as ET
import traceback
import time

class gmail_notify(base.base_plugin):
	
	def plugin_init(self):
		self.description = 'Google Talk Gmail Notification'
		self.xmpp.add_event_handler('sent_presence', self.handler_gmailcheck, threaded=True)
		self.emails = []
	
	def handler_gmailcheck(self, payload):
		#TODO XEP 30 should cache results and have getFeature
		result = self.xmpp['xep_0030'].getInfo(self.xmpp.server)
		features = []
		for feature in result.findall('{http://jabber.org/protocol/disco#info}query/{http://jabber.org/protocol/disco#info}feature'):
			features.append(feature.get('var'))
		if 'google:mail:notify' in features:
			logging.debug("Server supports Gmail Notify")
			self.xmpp.add_handler("<iq type='set' xmlns='%s'><new-mail xmlns='google:mail:notify' /></iq>" % self.xmpp.default_ns, self.handler_notify)
			self.getEmail()
	
	def handler_notify(self, xml):
		logging.info("New Gmail recieved!")
		self.xmpp.event('gmail_notify')
		
	def getEmail(self):
		iq = self.xmpp.makeIqGet()
		iq.attrib['from'] = self.xmpp.fulljid
		iq.attrib['to'] = self.xmpp.jid
		self.xmpp.makeIqQuery(iq, 'google:mail:notify')
		emails = iq.send()
		mailbox = emails.find('{google:mail:notify}mailbox')
		total = int(mailbox.get('total-matched', 0))
		logging.info("%s New Gmail Messages" % total)
