from .. xmlstream.stanzabase import ElementBase, ET

class HTMLIM(ElementBase):
	namespace = 'http://jabber.org/protocol/xhtml-im'
	name = 'html'
	plugin_attrib = 'html'
	interfaces = set(('html'))

	def setHtml(self, html):
		if issinstance(html, str):
			html = ET.XML(html)
		if html.find('{http://www.w3.org/1999/xhtml}body') is None:
			body = ET.Element('{http://www.w3.org/1999/xhtml}body')
			body.append(html)
		else:
			body = html
		self.xml.append(html)
	
	def getHtml(self):
		html = self.xml.find('{http://www.w3.org/1999/xhtml}body')
		if html is None: return ''
		return __str__(html)
	
	def delHtml(self):
		return self.__del__()
