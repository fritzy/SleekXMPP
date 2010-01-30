import types

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
		if xmlns != ixmlns and ixmlns != u'' and ixmlns != self.namespace:
			if self.stream is not None and ixmlns in self.stream.namespace_map:
				if self.stream.namespace_map[ixmlns] != u'':
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
			newoutput.append(u">")
			if xml.text:
				newoutput.append(self.xmlesc(xml.text))
			if len(xml):
				for child in xml.getchildren():
					newoutput.append(self.__str__(child, ixmlns))
			newoutput.append(u"</%s>" % (itag, ))
			if xml.tail:
				newoutput.append(self.xmlesc(xml.tail))
		elif xml.text:
			newoutput.append(">%s</%s>" % (self.xmlesc(xml.text), itag))
		else:
			newoutput.append(" />")
		return u''.join(newoutput)

	def xmlesc(self, text):
		if type(text) != types.UnicodeType:
			text = list(unicode(text, 'utf-8', 'ignore'))
		else:
			text = list(text)

		cc = 0
		matches = (u'&', u'<', u'"', u'>', u"'")
		for c in text:
			if c in matches:
				if c == u'&':
					text[cc] = u'&amp;'
				elif c == u'<':
					text[cc] = u'&lt;'
				elif c == u'>':
					text[cc] = u'&gt;'
				elif c == u"'":
					text[cc] = u'&apos;'
				else:
					text[cc] = u'&quot;'
			cc += 1
		return ''.join(text)
