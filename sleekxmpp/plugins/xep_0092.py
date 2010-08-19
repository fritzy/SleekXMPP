"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    This file is part of SleekXMPP.
    
    See the file LICENSE for copying permission.
"""
from xml.etree import cElementTree as ET
from . import base
from .. xmlstream.handler.xmlwaiter import XMLWaiter

class xep_0092(base.base_plugin):
	"""
	XEP-0092 Software Version
	"""
	def plugin_init(self):
		self.description = "Software Version"
		self.xep = "0092"
		self.name = self.config.get('name', 'SleekXMPP')
		self.version = self.config.get('version', '0.1-dev')
		self.xmpp.add_handler("<iq type='get' xmlns='%s'><query xmlns='jabber:iq:version' /></iq>" % self.xmpp.default_ns, self.report_version, name='Sofware Version')
	
	def post_init(self):
		base.base_plugin.post_init(self)
		self.xmpp.plugin['xep_0030'].add_feature('jabber:iq:version')
	
	def report_version(self, xml):
		iq = self.xmpp.makeIqResult(xml.get('id', 'unknown'))
		iq.attrib['to'] = xml.get('from', self.xmpp.server)
		query = ET.Element('{jabber:iq:version}query')
		name = ET.Element('name')
		name.text = self.name
		version = ET.Element('version')
		version.text = self.version
		query.append(name)
		query.append(version)
		iq.append(query)
		self.xmpp.send(iq)
	
	def getVersion(self, jid):
		iq = self.xmpp.makeIqGet()
		query = ET.Element('{jabber:iq:version}query')
		iq.append(query)
		iq.attrib['to'] = jid
		iq.attrib['from'] = self.xmpp.fulljid
		id = iq.get('id')
		result = iq.send()
		if result and result is not None and result.get('type', 'error') != 'error':
			qry = result.find('{jabber:iq:version}query')
			version = {}
			for child in qry.getchildren():
				version[child.tag.split('}')[-1]] = child.text
			return version
		else:
			return False

