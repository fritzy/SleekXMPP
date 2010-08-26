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

    """
    The core of SleekXMPP's stanza XML manipulation and handling is provided
    by ElementBase. ElementBase wraps XML cElementTree objects and enables
    access to the XML contents through dictionary syntax, similar in style
    to the Ruby XMPP library Blather's stanza implementation.

    Stanzas are defined by their name, namespace, and interfaces. For
    example, a simplistic Message stanza could be defined as:

    >>> class Message(ElementBase):
    ...     name = "message"
    ...     namespace = "jabber:client"
    ...     interfaces = set(('to', 'from', 'type', 'body'))
    ...     sub_interfaces = set(('body',))

    The resulting Message stanza's contents may be accessed as so:

    >>> message['to'] = "user@example.com"
    >>> message['body'] = "Hi!"

    The interface values map to either custom access methods, stanza
    XML attributes, or (if the interface is also in sub_interfaces) the
    text contents of a stanza's subelement.

    Custom access methods may be created by adding methods of the
    form "getInterface", "setInterface", or "delInterface", where
    "Interface" is the  titlecase version of the interface name.

    Stanzas may be extended through the use of plugins. A plugin
    is simply a stanza that has a plugin_attrib value. For example:

    >>> class MessagePlugin(ElementBase):
    ...     name = "custom_plugin"
    ...     namespace = "custom"
    ...     interfaces = set(('useful_thing', 'custom'))
    ...     plugin_attrib = "custom"

    The plugin stanza class must be associated with its intended
    container stanza by using registerStanzaPlugin as so:

    >>> registerStanzaPlugin(Message, MessagePlugin)

    The plugin may then be accessed as if it were built-in to the parent
    stanza.

    >>> message['custom']['useful_thing'] = 'foo'

    If a plugin provides an interface that is the same as the plugin's
    plugin_attrib value, then the plugin's interface may be accessed
    directly from the parent stanza, as so:

    >>> message['custom'] = 'bar' # Same as using message['custom']['custom']

    Class Attributes:
        name              -- The name of the stanza's main element.
        namespace         -- The namespace of the stanza's main element.
        interfaces        -- A set of attribute and element names that may
                             be accessed using dictionary syntax.
        sub_interfaces    -- A subset of the set of interfaces which map
                             to subelements instead of attributes.
        subitem           -- A set of stanza classes which are allowed to
                             be added as substanzas.
        types             -- A set of generic type attribute values.
        plugin_attrib     -- The interface name that the stanza uses to be
                             accessed as a plugin from another stanza.
        plugin_attrib_map -- A mapping of plugin attribute names with the
                             associated plugin stanza classes.
        plugin_tag_map    -- A mapping of plugin stanza tag names with
                             the associated plugin stanza classes.

    Instance Attributes:
        xml               -- The stanza's XML contents.
        parent            -- The parent stanza of this stanza.
        plugins           -- A map of enabled plugin names with the
                             initialized plugin stanza objects.

    Methods:
        setup           -- Initialize the stanza's XML contents.
        enable          -- Instantiate a stanza plugin. Alias for initPlugin.
        initPlugin      -- Instantiate a stanza plugin.
        getStanzaValues -- Return a dictionary of stanza interfaces and
                           their values.
        setStanzaValues -- Set stanza interface values given a dictionary of
                           interfaces and values.
        __getitem__     -- Return the value of a stanza interface.
        __setitem__     -- Set the value of a stanza interface.
        __delitem__     -- Remove the value of a stanza interface.
        _setAttr        -- Set an attribute value of the main stanza element.
        _delAttr        -- Remove an attribute from the main stanza element.
        _getAttr        -- Return an attribute's value from the main
                           stanza element.
        _getSubText     -- Return the text contents of a subelement.
        _setSubText     -- Set the text contents of a subelement.
        _delSub         -- Remove a subelement.
        match           -- Compare the stanza against an XPath expression.
        find            -- Return subelement matching an XPath expression.
        findall         -- Return subelements matching an XPath expression.
        get             -- Return the value of a stanza interface, with an
                           optional default value.
        keys            -- Return the set of interface names accepted by
                           the stanza.
        append          -- Add XML content or a substanza to the stanza.
        appendxml       -- Add XML content to the stanza.
        pop             -- Remove a substanza.
        next            -- Return the next iterable substanza.
        _fix_ns         -- Apply the stanza's namespace to non-namespaced
                           elements in an XPath expression.
    """

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
        self._index = 0
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

    def _delSub(self, name, all=False):
        """
        Remove sub elements that match the given name or XPath.

        If the element is in a path, then any parent elements that become
        empty after deleting the element may also be deleted if requested
        by setting all=True.

        Arguments:
            name -- The name or XPath expression for the element(s) to remove.
            all  -- If True, remove all empty elements in the path to the
                    deleted element. Defaults to False.
        """
        name = self._fix_ns(name)
        path = name.split("/")
        original_target = path[-1]

        for level, _ in enumerate(path):
            # Generate the paths to the target elements and their parent.
            element_path = "/".join(path[:len(path) - level])
            parent_path = "/".join(path[:len(path) - level - 1])

            elements = self.xml.findall(element_path)
            parent = self.xml.find(parent_path)

            if elements:
                if parent is None:
                    parent = self.xml
                for element in elements:
                    if element.tag == original_target or not element.getchildren():
                        # Only delete the originally requested elements, and any
                        # parent elements that have become empty.
                        parent.remove(element)
            if not all:
                # If we don't want to delete elements up the tree, stop
                # after deleting the first level of elements.
                return

    def match(self, xpath):
        """
        Compare a stanza object with an XPath expression. If the XPath matches
        the contents of the stanza object, the match is successful.

        The XPath expression may include checks for stanza attributes.
        For example:
            presence@show=xa@priority=2/status
        Would match a presence stanza whose show value is set to 'xa', has a
        priority value of '2', and has a status element.

        Arguments:
            xpath -- The XPath expression to check against. It may be either a
                     string or a list of element names with attribute checks.
        """
        if isinstance(xpath, str):
            xpath = xpath.split('/')

        # Extract the tag name and attribute checks for the first XPath node.
        components = xpath[0].split('@')
        tag = components[0]
        attributes = components[1:]

        if tag not in (self.name, "{%s}%s" % (self.namespace, self.name),
                       self.plugins, self.plugin_attrib):
            # The requested tag is not in this stanza, so no match.
            return False

        # Check the rest of the XPath against any substanzas.
        matched_substanzas = False
        for substanza in self.iterables:
            if xpath[1:] == []:
                break
            matched_substanzas = substanza.match(xpath[1:])
            if matched_substanzas:
                break

        # Check attribute values.
        for attribute in attributes:
            name, value = attribute.split('=')
            if self[name] != value:
                return False

        # Attempt to continue matching the XPath using the stanza's plugins.
        if not matched_substanzas and len(xpath) > 1:
            # Convert {namespace}tag@attribs to just tag
            next_tag = xpath[1].split('@')[0].split('}')[-1]
            if next_tag in self.plugins:
                return self.plugins[next_tag].match(xpath[1:])
            else:
                return False

        # Everything matched.
        return True

    def find(self, xpath):
        """
        Find an XML object in this stanza given an XPath expression.

        Exposes ElementTree interface for backwards compatibility.

        Note that matching on attribute values is not supported in Python 2.6
        or Python 3.1

        Arguments:
            xpath -- An XPath expression matching a single desired element.
        """
        return self.xml.find(xpath)

    def findall(self, xpath):
        """
        Find multiple XML objects in this stanza given an XPath expression.

        Exposes ElementTree interface for backwards compatibility.

        Note that matching on attribute values is not supported in Python 2.6
        or Python 3.1.

        Arguments:
            xpath -- An XPath expression matching multiple desired elements.
        """
        return self.xml.findall(xpath)

    def get(self, key, default=None):
        """
        Return the value of a stanza interface. If the found value is None
        or an empty string, return the supplied default value.

        Allows stanza objects to be used like dictionaries.

        Arguments:
            key     -- The name of the stanza interface to check.
            default -- Value to return if the stanza interface has a value
                       of None or "". Will default to returning None.
        """
        value = self[key]
        if value is None or value == '':
            return default
        return value

    def keys(self):
        """
        Return the names of all stanza interfaces provided by the
        stanza object.

        Allows stanza objects to be used like dictionaries.
        """
        out = []
        out += [x for x in self.interfaces]
        out += [x for x in self.plugins]
        if self.iterables:
            out.append('substanzas')
        return out

    def append(self, item):
        """
        Append either an XML object or a substanza to this stanza object.

        If a substanza object is appended, it will be added to the list
        of iterable stanzas.

        Allows stanza objects to be used like lists.

        Arguments:
            item -- Either an XML object or a stanza object to add to
                    this stanza's contents.
        """
        if not isinstance(item, ElementBase):
            if type(item) == XML_TYPE:
                return self.appendxml(item)
            else:
                raise TypeError
        self.xml.append(item.xml)
        self.iterables.append(item)
        return self

    def appendxml(self, xml):
        """
        Append an XML object to the stanza's XML.

        The added XML will not be included in the list of
        iterable substanzas.

        Arguments:
            xml -- The XML object to add to the stanza.
        """
        self.xml.append(xml)
        return self

    def pop(self, index=0):
        """
        Remove and return the last substanza in the list of
        iterable substanzas.

        Allows stanza objects to be used like lists.

        Arguments:
            index -- The index of the substanza to remove.
        """
        substanza = self.iterables.pop(index)
        self.xml.remove(substanza.xml)
        return substanza

    def next(self):
        """
        Return the next iterable substanza.
        """
        return self.__next__()

    @property
    def attrib(self):
        """
        DEPRECATED

        For backwards compatibility, stanza.attrib returns the stanza itself.

        Older implementations of stanza objects used XML objects directly,
        requiring the use of .attrib to access attribute values.

        Use of the dictionary syntax with the stanza object itself for
        accessing stanza interfaces is preferred.
        """
        return self

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

    def __eq__(self, other):
        """
        Compare the stanza object with another to test for equality.

        Stanzas are equal if their interfaces return the same values,
        and if they are both instances of ElementBase.

        Arguments:
            other -- The stanza object to compare against.
        """
        if not isinstance(other, ElementBase):
            return False

        # Check that this stanza is a superset of the other stanza.
        values = self.getStanzaValues()
        for key in other.keys():
            if key not in values or values[key] != other[key]:
                return False

        # Check that the other stanza is a superset of this stanza.
        values = other.getStanzaValues()
        for key in self.keys():
            if key not in values or values[key] != self[key]:
                return False

        # Both stanzas are supersets of each other, therefore they
        # must be equal.
        return True

    def __ne__(self, other):
        """
        Compare the stanza object with another to test for inequality.

        Stanzas are not equal if their interfaces return different values,
        or if they are not both instances of ElementBase.

        Arguments:
            other -- The stanza object to compare against.
        """
        return not self.__eq__(other)

    def __bool__(self):
        """
        Stanza objects should be treated as True in boolean contexts.

        Python 3.x version.
        """
        return True

    def __nonzero__(self):
        """
        Stanza objects should be treated as True in boolean contexts.

        Python 2.x version.
        """
        return True

    def __len__(self):
        """
        Return the number of iterable substanzas contained in this stanza.
        """
        return len(self.iterables)

    def __iter__(self):
        """
        Return an iterator object for iterating over the stanza's substanzas.

        The iterator is the stanza object itself. Attempting to use two
        iterators on the same stanza at the same time is discouraged.
        """
        self._index = 0
        return self

    def __next__(self):
        """
        Return the next iterable substanza.
        """
        self._index += 1
        if self._index > len(self.iterables):
            self._index = 0
            raise StopIteration
        return self.iterables[self._index - 1]

    def __copy__(self):
        """
        Return a copy of the stanza object that does not share the same
        underlying XML object.
        """
        return self.__class__(xml=copy.deepcopy(self.xml), parent=self.parent)

    def __str__(self):
        """
        Return a string serialization of the underlying XML object.
        """
        return tostring(self.xml, xmlns='', stanza_ns=self.namespace)

    def __repr__(self):
        """
        Use the stanza's serialized XML as its representation.
        """
        return self.__str__()


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
