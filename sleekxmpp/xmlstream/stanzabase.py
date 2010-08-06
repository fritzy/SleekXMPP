"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""
from xml.etree import cElementTree as ET
import logging
import sys
import weakref
import copy
from . jid import JID

from sleekxmpp.xmlstream.tostring import tostring

xmltester = type(ET.Element('xml'))


def registerStanzaPlugin(stanza, plugin):
        """
        Associate a stanza object as a plugin for another stanza.
        """
        tag = "{%s}%s" % (plugin.namespace, plugin.name)
        stanza.plugin_attrib_map[plugin.plugin_attrib] = plugin
        stanza.plugin_tag_map[tag] = plugin


class ElementBase(object):
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
                if parent is None:
                        self.parent = None
                else:
                        self.parent = weakref.ref(parent)
                self.xml = xml
                self.plugins = {}
                self.iterables = []
                self.idx = 0
                if not self.setup(xml):
                        for child in self.xml.getchildren():
                                if child.tag in self.plugin_tag_map:
                                        self.plugins[self.plugin_tag_map[child.tag].plugin_attrib] = self.plugin_tag_map[child.tag](xml=child, parent=self)
                                if self.subitem is not None:
                                        for sub in self.subitem:
                                                if child.tag == "{%s}%s" % (sub.namespace, sub.name):
                                                        self.iterables.append(sub(xml=child, parent=self))
                                                        break


        @property
        def attrib(self): #backwards compatibility
                return self

        def __iter__(self):
                self.idx = 0
                return self

        def __bool__(self):
                return True

        def __next__(self):
                self.idx += 1
                if self.idx > len(self.iterables):
                        self.idx = 0
                        raise StopIteration
                return self.iterables[self.idx - 1]

        def next(self):
                return self.__next__()

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
                if tagargs[0] not in (self.plugins, self.plugin_attrib): return False
                founditerable = False
                for iterable in self.iterables:
                        if nodes[1:] == []:
                                break
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

        def findall(self, xpath):
                return self.xml.findall(xpath)

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
                                self.parent().xml.append(self.xml)
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
                if not isinstance(other, ElementBase):
                        return False
                values = self.getStanzaValues()
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

        def _getAttr(self, name, default=''):
                return self.xml.attrib.get(name, default)

        def _getSubText(self, name):
                if '}' not in name:
                        name = "{%s}%s" % (self.namespace, name)
                stanza = self.xml.find(name)
                if stanza is None or stanza.text is None:
                        return ''
                else:
                        return stanza.text

        def _setSubText(self, name, attrib={}, text=None):
                if '}' not in name:
                        name = "{%s}%s" % (self.namespace, name)
                if text is None or text == '':
                        return self.__delitem__(name)
                stanza = self.xml.find(name)
                if stanza is None:
                        stanza = ET.Element(name)
                        self.xml.append(stanza)
                stanza.text = text
                return stanza

        def _delSub(self, name):
                if '}' not in name:
                        name = "{%s}%s" % (self.namespace, name)
                for child in self.xml.getchildren():
                        if child.tag == name:
                                self.xml.remove(child)

        def getStanzaValues(self):
                out = {}
                for interface in self.interfaces:
                        out[interface] = self[interface]
                for pluginkey in self.plugins:
                        out[pluginkey] = self.plugins[pluginkey].getStanzaValues()
                if self.iterables:
                        iterables = []
                        for stanza in self.iterables:
                                iterables.append(stanza.getStanzaValues())
                                iterables[-1].update({'__childtag__': "{%s}%s" % (stanza.namespace, stanza.name)})
                        out['substanzas'] = iterables
                return out

        def setStanzaValues(self, attrib):
                for interface in attrib:
                        if interface == 'substanzas':
                                for subdict in attrib['substanzas']:
                                        if '__childtag__' in subdict:
                                                for subclass in self.subitem:
                                                        if subdict['__childtag__'] == "{%s}%s" % (subclass.namespace, subclass.name):
                                                                sub = subclass(parent=self)
                                                                sub.setStanzaValues(subdict)
                                                                self.iterables.append(sub)
                                                                break
                        elif interface in self.interfaces:
                                self[interface] = attrib[interface]
                        elif interface in self.plugin_attrib_map and interface not in self.plugins:
                                self.initPlugin(interface)
                        if interface in self.plugins:
                                self.plugins[interface].setStanzaValues(attrib[interface])
                return self

        def appendxml(self, xml):
                self.xml.append(xml)
                return self

        def __copy__(self):
                return self.__class__(xml=copy.deepcopy(self.xml), parent=self.parent)

        def __str__(self):
                return tostring(self.xml, xmlns='', stanza_ns=self.namespace)

        def __repr__(self):
                return self.__str__()

        #def __del__(self): #prevents garbage collection of reference cycle
        #       if self.parent is not None:
        #               self.parent.xml.remove(self.xml)

class StanzaBase(ElementBase):
        name = 'stanza'
        namespace = 'jabber:client'
        interfaces = set(('type', 'to', 'from', 'id', 'payload'))
        types = set(('get', 'set', 'error', None, 'unavailable', 'normal', 'chat'))
        sub_interfaces = tuple()

        def __init__(self, stream=None, xml=None, stype=None, sto=None, sfrom=None, sid=None):
                self.stream = stream
                if stream is not None:
                        self.namespace = stream.default_ns
                ElementBase.__init__(self, xml)
                if stype is not None:
                        self['type'] = stype
                if sto is not None:
                        self['to'] = sto
                if sfrom is not None:
                        self['from'] = sfrom
                self.tag = "{%s}%s" % (self.namespace, self.name)

        def setType(self, value):
                if value in self.types:
                        self.xml.attrib['type'] = value
                return self

        def getPayload(self):
                return self.xml.getchildren()

        def setPayload(self, value):
                self.xml.append(value)
                return self

        def delPayload(self):
                self.clear()
                return self

        def clear(self):
                for child in self.xml.getchildren():
                        self.xml.remove(child)
                for plugin in list(self.plugins.keys()):
                        del self.plugins[plugin]
                return self

        def reply(self):
                # if it's a component, use from
                if self.stream and hasattr(self.stream, "is_component") and self.stream.is_component:
                        self['from'], self['to'] = self['to'], self['from']
                else:
                        self['to'] = self['from']
                        del self['from']
                self.clear()
                return self

        def error(self):
                self['type'] = 'error'
                return self

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
                logging.exception('Error handling {%s}%s stanza' % (self.namespace, self.name))

        def send(self):
                self.stream.sendRaw(self.__str__())

        def __copy__(self):
                return self.__class__(xml=copy.deepcopy(self.xml), stream=self.stream)

        def __str__(self):
                return tostring(self.xml, xmlns='', stanza_ns=self.namespace, stream=self.stream)
