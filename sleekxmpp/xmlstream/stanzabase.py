"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import copy
import logging
import sys
import weakref
from xml.etree import cElementTree as ET

from sleekxmpp.xmlstream import JID
from sleekxmpp.xmlstream.tostring import tostring


# Used to check if an argument is an XML object.
XML_TYPE = type(ET.Element('xml'))


def registerStanzaPlugin(stanza, plugin):
    """
    Associate a stanza object as a plugin for another stanza.

    Arguments:
        stanza -- The class of the parent stanza.
        plugin -- The class of the plugin stanza.
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
        """
        Create a new stanza object.

        Arguments:
            xml    -- Initialize the stanza with optional existing XML.
            parent -- Optional stanza object that contains this stanza.
        """
        self.xml = xml
        self.plugins = {}
        self.iterables = []
        self.idx = 0
        if parent is None:
            self.parent = None
        else:
            self.parent = weakref.ref(parent)

        if self.setup(xml):
            # If we generated our own XML, then everything is ready.
            return

        # Initialize values using provided XML
        for child in self.xml.getchildren():
            if child.tag in self.plugin_tag_map:
                plugin = self.plugin_tag_map[child.tag]
                self.plugins[plugin.plugin_attrib] = plugin(child, self)
            if self.subitem is not None:
                for sub in self.subitem:
                    if child.tag == "{%s}%s" % (sub.namespace, sub.name):
                        self.iterables.append(sub(child, self))
                        break

    def setup(self, xml=None):
        """
        Initialize the stanza's XML contents.

        Will return True if XML was generated according to the stanza's
        definition.

        Arguments:
            xml -- Optional XML object to use for the stanza's content
                   instead of generating XML.
        """
        if self.xml is None:
            self.xml = xml

        if self.xml is None:
            # Generate XML from the stanza definition
            for ename in self.name.split('/'):
                new = ET.Element("{%s}%s" % (self.namespace, ename))
                if self.xml is None:
                    self.xml = new
                else:
                    last_xml.append(new)
                last_xml = new
            if self.parent is not None:
                self.parent().xml.append(self.xml)

            # We had to generate XML
            return True
        else:
            # We did not generate XML
            return False

    def enable(self, attrib):
        """
        Enable and initialize a stanza plugin.

        Alias for initPlugin.

        Arguments:
            attrib -- The stanza interface for the plugin.
        """
        return self.initPlugin(attrib)

    def initPlugin(self, attrib):
        """
        Enable and initialize a stanza plugin.

        Arguments:
            attrib -- The stanza interface for the plugin.
        """
        if attrib not in self.plugins:
            plugin_class = self.plugin_attrib_map[attrib]
            self.plugins[attrib] = plugin_class(parent=self)
        return self

    def getStanzaValues(self):
        """
        Return a dictionary of the stanza's interface values.

        Stanza plugin values are included as nested dictionaries.
        """
        values = {}
        for interface in self.interfaces:
            values[interface] = self[interface]
        for plugin, stanza in self.plugins.items():
            values[plugin] = stanza.getStanzaValues()
        if self.iterables:
            iterables = []
            for stanza in self.iterables:
                iterables.append(stanza.getStanzaValues())
                iterables[-1].update({
                    '__childtag__': "{%s}%s" % (stanza.namespace, stanza.name)
                    })
            values['substanzas'] = iterables
        return values

    def setStanzaValues(self, values):
        """
        Set multiple stanza interface values using a dictionary.

        Stanza plugin values may be set using nested dictionaries.

        Arguments:
            values -- A dictionary mapping stanza interface with values.
                      Plugin interfaces may accept a nested dictionary that
                      will be used recursively.
        """
        for interface, value in values.items():
            if interface == 'substanzas':
                for subdict in value:
                    if '__childtag__' in subdict:
                        for subclass in self.subitem:
                            child_tag = "{%s}%s" % (subclass.namespace,
                                                    subclass.name)
                            if subdict['__childtag__'] == child_tag:
                                sub = subclass(parent=self)
                                sub.setStanzaValues(subdict)
                                self.iterables.append(sub)
                                break
            elif interface in self.interfaces:
                self[interface] = value
            elif interface in self.plugin_attrib_map:
                if interface not in self.plugins:
                    self.initPlugin(interface)
                self.plugins[interface].setStanzaValues(value)
        return self

    def __getitem__(self, attrib):
        """
        Return the value of a stanza interface using dictionary-like syntax.

        Example:
            >>> msg['body']
            'Message contents'

        Stanza interfaces are typically mapped directly to the underlying XML
        object, but can be overridden by the presence of a getAttrib method
        (or getFoo where the interface is named foo, etc).

        The search order for interface value retrieval for an interface
        named 'foo' is:
            1. The list of substanzas.
            2. The result of calling getFoo.
            3. The contents of the foo subelement, if foo is a sub interface.
            4. The value of the foo attribute of the XML object.
            5. The plugin named 'foo'
            6. An empty string.

        Arguments:
            attrib -- The name of the requested stanza interface.
        """
        if attrib == 'substanzas':
            return self.iterables
        elif attrib in self.interfaces:
            get_method = "get%s" % attrib.title()
            if hasattr(self, get_method):
                return getattr(self, get_method)()
            else:
                if attrib in self.sub_interfaces:
                    return self._getSubText(attrib)
                else:
                    return self._getAttr(attrib)
        elif attrib in self.plugin_attrib_map:
            if attrib not in self.plugins:
                self.initPlugin(attrib)
            return self.plugins[attrib]
        else:
            return ''

    def __setitem__(self, attrib, value):
        """
        Set the value of a stanza interface using dictionary-like syntax.

        Example:
            >>> msg['body'] = "Hi!"
            >>> msg['body']
            'Hi!'

        Stanza interfaces are typically mapped directly to the underlying XML
        object, but can be overridden by the presence of a setAttrib method
        (or setFoo where the interface is named foo, etc).

        The effect of interface value assignment for an interface
        named 'foo' will be one of:
            1. Delete the interface's contents if the value is None.
            2. Call setFoo, if it exists.
            3. Set the text of a foo element, if foo is in sub_interfaces.
            4. Set the value of a top level XML attribute name foo.
            5. Attempt to pass value to a plugin named foo using the plugin's
               foo interface.
            6. Do nothing.

        Arguments:
            attrib -- The name of the stanza interface to modify.
            value  -- The new value of the stanza interface.
        """
        if attrib in self.interfaces:
            if value is not None:
                set_method = "set%s" % attrib.title()
                if hasattr(self, set_method):
                    getattr(self, set_method)(value,)
                else:
                    if attrib in self.sub_interfaces:
                        return self._setSubText(attrib, text=value)
                    else:
                        self._setAttr(attrib, value)
            else:
                self.__delitem__(attrib)
        elif attrib in self.plugin_attrib_map:
            if attrib not in self.plugins:
                self.initPlugin(attrib)
            self.plugins[attrib][attrib] = value
        return self

    def __delitem__(self, attrib):
        """
        Delete the value of a stanza interface using dictionary-like syntax.

        Example:
            >>> msg['body'] = "Hi!"
            >>> msg['body']
            'Hi!'
            >>> del msg['body']
            >>> msg['body']
            ''

        Stanza interfaces are typically mapped directly to the underlyig XML
        object, but can be overridden by the presence of a delAttrib method
        (or delFoo where the interface is named foo, etc).

        The effect of deleting a stanza interface value named foo will be
        one of:
            1. Call delFoo, if it exists.
            2. Delete foo element, if foo is in sub_interfaces.
            3. Delete top level XML attribute named foo.
            4. Remove the foo plugin, if it was loaded.
            5. Do nothing.

        Arguments:
            attrib -- The name of the affected stanza interface.
        """
        if attrib in self.interfaces:
            del_method = "del%s" % attrib.title()
            if hasattr(self, del_method):
                getattr(self, del_method)()
            else:
                if attrib in self.sub_interfaces:
                    return self._delSub(attrib)
                else:
                    self._delAttr(attrib)
        elif attrib in self.plugin_attrib_map:
            if attrib in self.plugins:
                del self.plugins[attrib]
        return self

    def _setAttr(self, name, value):
        """
        Set the value of a top level attribute of the underlying XML object.

        If the new value is None or an empty string, then the attribute will
        be removed.

        Arguments:
            name  -- The name of the attribute.
            value -- The new value of the attribute, or None or '' to
                     remove it.
        """
        if value is None or value == '':
            self.__delitem__(name)
        else:
            self.xml.attrib[name] = value

    def _delAttr(self, name):
        """
        Remove a top level attribute of the underlying XML object.

        Arguments:
            name -- The name of the attribute.
        """
        if name in self.xml.attrib:
            del self.xml.attrib[name]

    def _getAttr(self, name, default=''):
        """
        Return the value of a top level attribute of the underlying
        XML object.

        In case the attribute has not been set, a default value can be
        returned instead. An empty string is returned if no other default
        is supplied.

        Arguments:
            name    -- The name of the attribute.
            default -- Optional value to return if the attribute has not
                       been set. An empty string is returned otherwise.
        """
        return self.xml.attrib.get(name, default)

    def _getSubText(self, name, default=''):
      """
      Return the text contents of a sub element.

      In case the element does not exist, or it has no textual content,
      a default value can be returned instead. An empty string is returned 
      if no other default is supplied.

      Arguments:
          name    -- The name or XPath expression of the element.
          default -- Optional default to return if the element does
                     not exists. An empty string is returned otherwise.
      """
      name = self._fix_ns(name)
      stanza = self.xml.find(name)
      if stanza is None or stanza.text is None:
          return default
      else:
          return stanza.text

    def _setSubText(self, name, text=None, keep=False):
        """
        Set the text contents of a sub element.

        In case the element does not exist, a element will be created,
        and its text contents will be set.

        If the text is set to an empty string, or None, then the 
        element will be removed, unless keep is set to True.

        Arguments:
            name -- The name or XPath expression of the element.
            text -- The new textual content of the element. If the text
                    is an empty string or None, the element will be removed
                    unless the parameter keep is True.
            keep -- Indicates if the element should be kept if its text is
                    removed. Defaults to False.
        """
        name = self._fix_ns(name)
        element = self.xml.find(name)

        if not text and not keep:
            return self.__delitem__(name)

        if element is None:
            # We need to add the element. If the provided name was
            # an XPath expression, some of the intermediate elements
            # may already exist. If so, we want to use those instead
            # of generating new elements.
            last_xml = self.xml
            walked = []
            for ename in name.split('/'):
                walked.append(ename)
                element = self.xml.find("/".join(walked))
                if element is None:
                    element = ET.Element(ename)
                    last_xml.append(element)
                last_xml = element
            element = last_xml

        element.text = text
        return element 

    @property
    def attrib(self): #backwards compatibility
            return self

    def __iter__(self):
            self.idx = 0
            return self

    def __bool__(self): #python 3.x
            return True
    
    def __nonzero__(self): #python 2.x
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
                    if type(item) == XML_TYPE:
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

    def __eq__(self, other):
            if not isinstance(other, ElementBase):
                    return False
            values = self.getStanzaValues()
            for key in other:
                    if key not in values or values[key] != other[key]:
                            return False
            return True

    def _delSub(self, name):
            if '}' not in name:
                    name = "{%s}%s" % (self.namespace, name)
            for child in self.xml.getchildren():
                    if child.tag == name:
                            self.xml.remove(child)

    def appendxml(self, xml):
            self.xml.append(xml)
            return self

    def __copy__(self):
            return self.__class__(xml=copy.deepcopy(self.xml), parent=self.parent)

    def __str__(self):
            return tostring(self.xml, xmlns='', stanza_ns=self.namespace)

    def __repr__(self):
            return self.__str__()

    def _fix_ns(self, xpath):
        """
        Apply the stanza's namespace to elements in an XPath expression.

        Arguments:
            xpath -- The XPath expression to fix with namespaces.
        """

        def fix_ns(name):
            """Apply namespace to an element if needed."""
            if "}" in name:
                return name
            return "{%s}%s" % (self.namespace, name)

        return "/".join(map(fix_ns, xpath.split("/")))
        

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
