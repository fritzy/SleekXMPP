
class ToString(object):
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
		if xmlns != ixmlns and ixmlns != '' and ixmlns != self.namespace:
			if self.stream is not None and ixmlns in self.stream.namespace_map:
				if self.stream.namespace_map[ixmlns] != '':
					itag = "%s:%s" % (self.stream.namespace_map[ixmlns], itag)
			else:
				nsbuffer = """ xmlns="%s\"""" % ixmlns
		if ixmlns not in ('', xmlns, self.namespace):
			nsbuffer = """ xmlns="%s\"""" % ixmlns
		newoutput.append("<%s" % itag)
		newoutput.append(nsbuffer)
		for attrib in xml.attrib:
			if '{' not in attrib:
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
				else:
					text[cc] = '&quot;'
			cc += 1
		return ''.join(text)
