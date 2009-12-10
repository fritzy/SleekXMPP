from xml.etree import cElementTree as ET

class StanzaBase(object):
	name = 'stanza'
	namespace = 'jabber:client'
	interfaces = set(('type', 'to', 'from', 'id', 'payload'))
	types = set(('get', 'set', 'error', None, 'unavailable', 'normal', 'chat'))
	sub_interfaces = tuple()

	def __init__(self, stream, xml=None, stype=None, sto=None, sfrom=None, sid=None):
		self.stream = stream
		self.xml = xml
		if xml is None:
			self.xml = ET.Element("{%(namespace)s}%(name)s" % {'name': self.name, 'namespace': self.namespace})
		if stype is not None:
			self['type'] = stype
		if sto is not None:
			self['to'] = sto
		if sfrom is not None:
			self['from'] = sfrom
		self.tag = "{%s}%s" % (self.stream.default_ns, self.name)
	
	def match(self, xml):
		return xml.tag == self.tag
		
	def __getitem__(self, attrib):
		if attrib in self.interfaces:
			if hasattr(self, "get%s" % attrib.title()):
				return getattr(self, "get%s" % attrib.title())()
			else:
				if attrib in self.sub_interfaces:
					return self._getSubText(attrib)
				else:
					return self._getAttr(attrib)
		else:
			return ''
	
	def __setitem__(self, attrib, value):
		if attrib.lower() in self.interfaces:
			if value is not None:
				if hasattr(self, "set%s" % attrib.title()):
					getattr(self, "set%s" % attrib.title())(value,)
				else:
					if attrib in self.sub_interfaces:
						return self._setSubText(attrib, text=value)
					else:
						self._setAttr(attrib, value)
			else:
				self.__delitem__(attrib)
		return self
	
	def __delitem__(self, attrib):
		if attrib.lower() in self.interfaces:
			if hasattr(self, "del%s" % attrib.title()):
				getattr(self, "del%s" % attrib.title())()
			else:
				if attrib in self.sub_interfaces:
					return self._delSub(attrib)
				else:
					self._delAttr(attrib)
		return self

	def setType(self, value):
		if value in self.types:
			if value is None and 'type' in self.xml.attrib:
				del self.xml.attrib['type']
			elif value is not None:
				self.xml.attrib['type'] = value
		else:
			raise ValueError
		return self

	def getPayload(self):
		return self.xml.getchildren()
	
	def setPayload(self, value):
		self.xml.append(value)
	
	def delPayload(self):
		self.clear()
	
	def clear(self):
		for child in self.xml.getchildren():
			self.xml.remove(child)
	
	def reply(self):
		self['from'], self['to'] = self['to'], self['from']
		return self
	
	def error(self):
		self['type'] = 'error'
	
	def _setAttr(self, name, value):
		self.xml.attrib[name] = value
	
	def _delAttr(self, name):
		if name in self.xml.attrib:
			del self.xml.attrib[name]
	
	def _getAttr(self, name):
		return self.xml.attrib.get(name, '')
	
	def _getSubText(self, name):
		stanza = self.xml.find("{%s}%s" % (self.namespace, name))
		if stanza is None or stanza.text is None:
			return ''
		else:
			return stanza.text
	
	def _setSubText(self, name, attrib={}, text=None):
		stanza = self.xml.find("{%s}%s" % (self.namespace, name))
		if stanza is None:
			self.xml.append(ET.Element("{%s}%s" % (self.namespace, name), attrib))
			stanza = self.xml.find("{%s}%s" % (self.namespace, name))
		if text is not None:
			stanza.text = text
		return stanza
		
	def _delSub(self, name):
		for child in self.xml.getchildren():
			if child.tag == "{%s}%s" % (self.namespace, name):
				self.xml.remove(child)
	
	def unhandled(self):
		pass
	
	def send(self):
		self.stream.sendRaw(str(self))

	def __str__(self, xml=None, xmlns='', stringbuffer=''):
		if xml is None:
			xml = self.xml
		newoutput = [stringbuffer]
		#TODO respect ET mapped namespaces
		itag = xml.tag.split('}', 1)[-1]
		if '}' in xml.tag:
			ixmlns = xml.tag.split('}', 1)[0][1:]
		else:
			ixmlns = ''
		nsbuffer = ''
		#if xmlns != ixmlns and ixmlns != '':
		#	if ixmlns in self.namespace_map:
		#		if self.namespace_map[ixmlns] != '':
		#			itag = "%s:%s" % (self.namespace_map[ixmlns], itag)
		#	else:
		#		nsbuffer = """ xmlns="%s\"""" % ixmlns
		if ixmlns not in (xmlns, self.namespace):
			nsbuffer = """ xmlns="%s\"""" % ixmlns
		newoutput.append("<%s" % itag)
		newoutput.append(nsbuffer)
		for attrib in xml.attrib:
			newoutput.append(""" %s="%s\"""" % (attrib, self.xmlesc(xml.attrib[attrib])))
		if len(xml) or xml.text or xml.tail:
			newoutput.append(">")
			if xml.text:
				newoutput.append(self.xmlesc(xml.text))
			if len(xml):
				for child in xml.getchildren():
					newoutput.append(self.__str__(child, ixmlns))
			newoutput.append("</%s>" % (itag, ))
			if xml.tail:
				newoutput.append(self.xmlesc(xml.tail))
		elif xml.text:
			newoutput.append(">%s</%s>" % (self.xmlesc(xml.text), itag))
		else:
			newoutput.append(" />")
		return ''.join(newoutput)

	def xmlesc(self, text):
		text = list(text)
		cc = 0
		matches = ('&', '<', '"', '>', "'")
		for c in text:
			if c in matches:
				if c == '&':
					text[cc] = '&amp;'
				elif c == '<':
					text[cc] = '&lt;'
				elif c == '>':
					text[cc] = '&gt;'
				elif c == "'":
					text[cc] = '&apos;'
				elif self.escape_quotes:
					text[cc] = '&quot;'
			cc += 1
		return ''.join(text)
		

if __name__ == '__main__':
	x = Stanza()
	x['from'] = 'you'
	x['to'] = 'me'
	print(x['from'], x['to'])
	x.reply()
	print(x['from'], x['to'])
	x['from'] = None
	print(x['from'], x['to'])
	print(str(x))
