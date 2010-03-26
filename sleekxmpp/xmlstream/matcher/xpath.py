"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from . import base
from xml.etree import cElementTree

ignore_ns = False

class MatchXPath(base.MatcherBase):

	def match(self, xml):
		if hasattr(xml, 'xml'):
			xml = xml.xml
		x = cElementTree.Element('x')
		x.append(xml)
		if not ignore_ns:
			if x.find(self._criteria) is not None:
				return True
			return False
		else:
			criteria = [c.split('}')[-1] for c in self._criteria.split('/')]
			xml = x
			for tag in criteria:
				children = [c.tag.split('}')[-1] for c in xml.getchildren()]
				try:
					idx = children.index(tag)
				except ValueError:
					return False
				xml = xml.getchildren()[idx]
			return True
