"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from .. xmlstream.stanzabase import ElementBase, ET

class Nick(ElementBase):
	namespace = 'http://jabber.org/nick/nick'
	name = 'nick'
	plugin_attrib = 'nick'
	interfaces = set(('nick'))
	plugin_attrib_map = set()
	plugin_xml_map = set()

	def setNick(self, nick):
		self.xml.text = nick
	
	def getNick(self):
		return self.xml.text
	
	def delNick(self):
		if self.parent is not None:
			self.parent().xml.remove(self.xml)
