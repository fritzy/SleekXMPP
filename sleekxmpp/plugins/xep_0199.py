"""
	SleekXMPP: The Sleek XMPP Library
	XEP-0199 (Ping) support
	Copyright (C) 2007  Kevin Smith
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
from xml.etree import cElementTree as ET
from . import base
import time
import logging

class xep_0199(base.base_plugin):
	"""XEP-0199 XMPP Ping"""

	def plugin_init(self):
		self.description = "XMPP Ping"
		self.xep = "0199"
		self.xmpp.add_handler("<iq type='get' xmlns='%s'><ping xmlns='http://www.xmpp.org/extensions/xep-0199.html#ns'/></iq>" % self.xmpp.default_ns, self.handler_ping)
		self.running = False
		#if self.config.get('keepalive', True):
			#self.xmpp.add_event_handler('session_start', self.handler_pingserver, threaded=True)
	
	def post_init(self):
		base.base_plugin.post_init(self)
		self.xmpp.plugin['xep_0030'].add_feature('http://www.xmpp.org/extensions/xep-0199.html#ns')
	
	def handler_pingserver(self, xml):
		if not self.running:
			time.sleep(self.config.get('frequency', 300))
			while self.sendPing(self.xmpp.server, self.config.get('timeout', 30)) is not False:
				time.sleep(self.config.get('frequency', 300))
			logging.debug("Did not recieve ping back in time.  Requesting Reconnect.")
			self.xmpp.disconnect(reconnect=True)
	
	def handler_ping(self, xml):
		iq = self.xmpp.makeIqResult(xml.get('id', 'unknown'))
		iq.attrib['to'] = xml.get('from', self.xmpp.server)
		self.xmpp.send(iq)

	def sendPing(self, jid, timeout = 30):
		""" sendPing(jid, timeout)
		Sends a ping to the specified jid, returning the time (in seconds)
		to receive a reply, or None if no reply is received in timeout seconds.
		"""
		id = self.xmpp.getNewId()
		iq = self.xmpp.makeIq(id)
		iq.attrib['type'] = 'get'
		iq.attrib['to'] = jid
		ping = ET.Element('{http://www.xmpp.org/extensions/xep-0199.html#ns}ping')
		iq.append(ping)
		startTime = time.clock()
		#pingresult = self.xmpp.send(iq, self.xmpp.makeIq(id), timeout)
		pingresult = iq.send()
		endTime = time.clock()
		if pingresult == False:
			#self.xmpp.disconnect(reconnect=True)
			return False
		return endTime - startTime
