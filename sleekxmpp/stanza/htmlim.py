"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from .. xmlstream.stanzabase import ElementBase, ET

class HTMLIM(ElementBase):
	namespace = 'http://jabber.org/protocol/xhtml-im'
	name = 'html'
	plugin_attrib = 'html'
	interfaces = set(('html',))
	plugin_attrib_map = set()
	plugin_xml_map = set()

	def setHtml(self, html):
		if isinstance(html, str):
			html = ET.XML(html)
		if html.tag != '{http://www.w3.org/1999/xhtml}body':
			body = ET.Element('{http://www.w3.org/1999/xhtml}body')
			body.append(html)
			self.xml.append(body)
		else:
			self.xml.append(html)
	
	def getHtml(self):
		html = self.xml.find('{http://www.w3.org/1999/xhtml}body')
		if html is None: return ''
		return html
	
	def delHtml(self):
		if self.parent is not None:
			self.parent().xml.remove(self.xml)
