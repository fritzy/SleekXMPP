"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from xml.etree import cElementTree as ET
import logging
import traceback
import sys

if sys.version_info < (3,0):
	from . import tostring26 as tostring
else:
	from . import tostring

xmltester = type(ET.Element('xml'))

class JID(object):
	def __init__(self, jid):
		self.jid = jid
	
	def __getattr__(self, name):
		if name == 'resource':
			return self.jid.split('/', 1)[-1]
		elif name == 'user':
			if '@' in self.jid:
				return self.jid.split('@', 1)[0]
			else:
				return ''
		elif name == 'server':
			return self.jid.split('@', 1)[-1].split('/', 1)[0]
		elif name == 'full':
			return self.jid
		elif name == 'bare':
			return self.jid.split('/', 1)[0]
	
	def __str__(self):
		return self.jid

class ElementBase(tostring.ToString):
	name = 'stanza'
	plugin_attrib = 'plugin'
	namespace = 'jabber:client'
	interfaces = set(('type', 'to', 'from', 'id', 'payload'))
	types = set(('get', 'set', 'error', None, 'unavailable', 'normal', 'chat'))
	sub_interfaces = tuple()
	plugin_attrib_map = {}
	plugin_tag_map = {}
	subitem = None

	def __init__(self, xml=None, parent=None):
		self.parent = parent
		self.xml = xml
		self.plugins = {}
		self.iterables = []
		self.idx = 0
		if not self.setup(xml):
			for child in self.xml.getchildren():
				if child.tag in self.plugin_tag_map:
					self.plugins[self.plugin_tag_map[child.tag].plugin_attrib] = self.plugin_tag_map[child.tag](xml=child, parent=self)
				if self.subitem is not None and child.tag == "{%s}%s" % (self.subitem.namespace, self.subitem.name):
					self.iterables.append(self.subitem(xml=child, parent=self))


	@property
	def attrib(self): #backwards compatibility
		return self

	def __iter__(self):
		self.idx = 0
		return self
	
	def __next__(self):
		self.idx += 1
		if self.idx + 1 > len(self.iterables):
			self.idx = 0
			raise StopIteration
		return self.affiliations[self.idx]
	
	def __len__(self):
		return len(self.iterables)
	
	def append(self, item):
		if not isinstance(item, ElementBase):
			if type(item) == xmltester:
				return self.appendxml(item)
			else:
				raise TypeError
		self.xml.append(item.xml)
		self.iterables.append(item)
		return self
	
	def pop(self, idx=0):
		aff = self.iterables.pop(idx)
		self.xml.remove(aff.xml)
		return aff
	
	def get(self, key, defaultvalue=None):
		value = self[key]
		if value is None or value == '':
			return defaultvalue
		return value
	
	def keys(self):
		out = []
		out += [x for x in self.interfaces]
		out += [x for x in self.plugins]
		if self.iterables:
			out.append('substanzas')
		return tuple(out)
	
	def match(self, matchstring):
		if isinstance(matchstring, str):
			nodes = matchstring.split('/')
		else:
			nodes = matchstring
		tagargs = nodes[0].split('@')
		if tagargs[0] not in (self.plugins, self.name): return False
		founditerable = False
		for iterable in self.iterables:
			founditerable = iterable.match(nodes[1:])
			if founditerable: break;
		for evals in tagargs[1:]:
			x,y = evals.split('=')
			if self[x] != y: return False
		if not founditerable and len(nodes) > 1:
			next = nodes[1].split('@')[0]
			if next in self.plugins:
				return self.plugins[next].match(nodes[1:])
			else:
				return False
		return True
	
	def find(self, xpath): # for backwards compatiblity, expose elementtree interface
		return self.xml.find(xpath)
	
	def setup(self, xml=None):
		if self.xml is None:
			self.xml = xml
		if self.xml is None:
			for ename in self.name.split('/'):
				new = ET.Element("{%(namespace)s}%(name)s" % {'name': self.name, 'namespace': self.namespace})
				if self.xml is None:
					self.xml = new
				else:
					self.xml.append(new)
			if self.parent is not None:
				self.parent.xml.append(self.xml)
			return True #had to generate XML
		else:
			return False

	def enable(self, attrib):
		self.initPlugin(attrib)
		return self
	
	def initPlugin(self, attrib):
		if attrib not in self.plugins:
			self.plugins[attrib] = self.plugin_attrib_map[attrib](parent=self)
	
	def __getitem__(self, attrib):
		if attrib == 'substanzas':
			return self.iterables
		elif attrib in self.interfaces:
			if hasattr(self, "get%s" % attrib.title()):
				return getattr(self, "get%s" % attrib.title())()
			else:
				if attrib in self.sub_interfaces:
					return self._getSubText(attrib)
				else:
					return self._getAttr(attrib)
		elif attrib in self.plugin_attrib_map:
			if attrib not in self.plugins: self.initPlugin(attrib)
			return self.plugins[attrib]
		else:
			return ''
	
	def __setitem__(self, attrib, value):
		if attrib in self.interfaces:
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
		elif attrib in self.plugin_attrib_map:
			if attrib not in self.plugins: self.initPlugin(attrib)
			self.initPlugin(attrib)
			self.plugins[attrib][attrib] = value
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
		elif attrib in self.plugin_attrib_map:
			if attrib in self.plugins:
				del self.plugins[attrib]
		return self
	
	def __eq__(self, other):
		values = self.getValues()
		for key in other:
			if key not in values or values[key] != other[key]:
				return False
		return True
	
	def _setAttr(self, name, value):
		if value is None or value == '':
			self.__delitem__(name)
		else:
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
		if text is None or text == '':
			return self.__delitem__(name)
		stanza = self.xml.find("{%s}%s" % (self.namespace, name))
		if stanza is None:
			#self.xml.append(ET.Element("{%s}%s" % (self.namespace, name), attrib))
			stanza = ET.Element("{%s}%s" % (self.namespace, name))
			self.xml.append(stanza)
		stanza.text = text
		return stanza
		
	def _delSub(self, name):
		for child in self.xml.getchildren():
			if child.tag == "{%s}%s" % (self.namespace, name):
				self.xml.remove(child)
	
	def getValues(self):
		out = {}
		for interface in self.interfaces:
			out[interface] = self[interface]
		for pluginkey in self.plugins:
			out[pluginkey] = self.plugins[pluginkey].getValues()
		if self.iterables:
			iterables = [x.getValues() for x in self.iterables]
			out['substanzas'] = iterables
		return out
	
	def setValues(self, attrib):
		for interface in attrib:
			if interface == 'substanzas':
				for subdict in attrib['substanzas']:
					sub = self.subitem(parent=self)
					sub.setValues(subdict)
					self.iterables.append(sub)
			elif interface in self.interfaces:
				self[interface] = attrib[interface]
			elif interface in self.plugin_attrib_map and interface not in self.plugins:
				self.initPlugin(interface)
			if interface in self.plugins:
				self.plugins[interface].setValues(attrib[interface])
		return self
	
	def appendxml(self, xml):
		self.xml.append(xml)
		return self
	
	def __del__(self):
		if self.parent is not None:
			self.parent.xml.remove(self.xml)

class StanzaBase(ElementBase):
	name = 'stanza'
	namespace = 'jabber:client'
	interfaces = set(('type', 'to', 'from', 'id', 'payload'))
	types = set(('get', 'set', 'error', None, 'unavailable', 'normal', 'chat'))
	sub_interfaces = tuple()

	def __init__(self, stream=None, xml=None, stype=None, sto=None, sfrom=None, sid=None):
		self.stream = stream
		ElementBase.__init__(self, xml)
		if stype is not None:
			self['type'] = stype
		if sto is not None:
			self['to'] = sto
		if sfrom is not None:
			self['from'] = sfrom
		if stream is not None:
			self.namespace = stream.default_ns
		self.tag = "{%s}%s" % (self.namespace, self.name)
	
	def setType(self, value):
		if value in self.types:
				self.xml.attrib['type'] = value
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
		#for plugin in list(self.plugins.keys()):
		#	del self.plugins[plugin]
	
	def reply(self):
		self['from'], self['to'] = self['to'], self['from']
		self.clear()
		return self
	
	def error(self):
		self['type'] = 'error'
	
	def getTo(self):
		return JID(self._getAttr('to'))
	
	def setTo(self, value):
		return self._setAttr('to', str(value))
	
	def getFrom(self):
		return JID(self._getAttr('from'))
	
	def setFrom(self, value):
		return self._setAttr('from', str(value))
	
	def unhandled(self):
		pass
	
	def exception(self, e):
		logging.error(traceback.format_tb(e))
	
	def send(self):
		self.stream.sendRaw(self.__str__())

