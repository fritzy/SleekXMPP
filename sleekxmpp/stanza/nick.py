from .. xmlstream.stanzabase import ElementBase, ET

class HTMLIM(ElementBase):
	namespace = 'http://jabber.org/nick/nick'
	name = 'nick'
	plugin_attrib = 'nick'
	interfaces = set(('nick'))

	def setNick(self, nick):
		self.xml.text = nick
	
	def getNick(self):
		return self.xml.text
	
	def delNick(self):
		return self.__del__()
