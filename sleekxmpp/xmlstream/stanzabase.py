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


log = logging.getLogger(__name__)


# Used to check if an argument is an XML object.
XML_TYPE = type(ET.Element('xml'))


def register_stanza_plugin(stanza, plugin):
    """
    Associate a stanza object as a plugin for another stanza.

    Arguments:
        stanza -- The class of the parent stanza.
        plugin -- The class of the plugin stanza.
    """
    tag = "{%s}%s" % (plugin.namespace, plugin.name)
    stanza.plugin_attrib_map[plugin.plugin_attrib] = plugin
    stanza.plugin_tag_map[tag] = plugin


# To maintain backwards compatibility for now, preserve the camel case name.
registerStanzaPlugin = register_stanza_plugin


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
    >>> message['body']
    "Hi!"
    >>> del message['body']
    >>> message['body']
    ""

    The interface values map to either custom access methods, stanza
    XML attributes, or (if the interface is also in sub_interfaces) the
    text contents of a stanza's subelement.

    Custom access methods may be created by adding methods of the
    form "getInterface", "setInterface", or "delInterface", where
    "Interface" is the titlecase version of the interface name.

    Stanzas may be extended through the use of plugins. A plugin
    is simply a stanza that has a plugin_attrib value. For example:

    >>> class MessagePlugin(ElementBase):
    ...     name = "custom_plugin"
    ...     namespace = "custom"
    ...     interfaces = set(('useful_thing', 'custom'))
    ...     plugin_attrib = "custom"

    The plugin stanza class must be associated with its intended
    container stanza by using register_stanza_plugin as so:

    >>> register_stanza_plugin(Message, MessagePlugin)

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
        values            -- A dictionary of the stanza's interfaces
                             and interface values, including plugins.

    Methods:
        setup              -- Initialize the stanza's XML contents.
        enable             -- Instantiate a stanza plugin.
                              Alias for init_plugin.
        init_plugin        -- Instantiate a stanza plugin.
        _get_stanza_values -- Return a dictionary of stanza interfaces and
                              their values.
        _set_stanza_values -- Set stanza interface values given a dictionary
                              of interfaces and values.
        __getitem__        -- Return the value of a stanza interface.
        __setitem__        -- Set the value of a stanza interface.
        __delitem__        -- Remove the value of a stanza interface.
        _set_attr          -- Set an attribute value of the main
                              stanza element.
        _del_attr          -- Remove an attribute from the main
                              stanza element.
        _get_attr          -- Return an attribute's value from the main
                              stanza element.
        _get_sub_text      -- Return the text contents of a subelement.
        _set_sub_ext       -- Set the text contents of a subelement.
        _del_sub           -- Remove a subelement.
        match              -- Compare the stanza against an XPath expression.
        find               -- Return subelement matching an XPath expression.
        findall            -- Return subelements matching an XPath expression.
        get                -- Return the value of a stanza interface, with an
                              optional default value.
        keys               -- Return the set of interface names accepted by
                              the stanza.
        append             -- Add XML content or a substanza to the stanza.
        appendxml          -- Add XML content to the stanza.
        pop                -- Remove a substanza.
        next               -- Return the next iterable substanza.
        _fix_ns            -- Apply the stanza's namespace to non-namespaced
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
        # To comply with PEP8, method names now use underscores.
        # Deprecated method names are re-mapped for backwards compatibility.
        self.initPlugin = self.init_plugin
        self._getAttr = self._get_attr
        self._setAttr = self._set_attr
        self._delAttr = self._del_attr
        self._getSubText = self._get_sub_text
        self._setSubText = self._set_sub_text
        self._delSub = self._del_sub
        self.getStanzaValues = self._get_stanza_values
        self.setStanzaValues = self._set_stanza_values

        self.xml = xml
        self.plugins = {}
        self.iterables = []
        self._index = 0
        if parent is None:
            self.parent = None
        else:
            self.parent = weakref.ref(parent)

        ElementBase.values = property(ElementBase._get_stanza_values,
                                      ElementBase._set_stanza_values)

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

        Alias for init_plugin.

        Arguments:
            attrib -- The stanza interface for the plugin.
        """
        return self.init_plugin(attrib)

    def init_plugin(self, attrib):
        """
        Enable and initialize a stanza plugin.

        Arguments:
            attrib -- The stanza interface for the plugin.
        """
        if attrib not in self.plugins:
            plugin_class = self.plugin_attrib_map[attrib]
            self.plugins[attrib] = plugin_class(parent=self)
        return self

    def _get_stanza_values(self):
        """
        Return a dictionary of the stanza's interface values.

        Stanza plugin values are included as nested dictionaries.
        """
        values = {}
        for interface in self.interfaces:
            values[interface] = self[interface]
        for plugin, stanza in self.plugins.items():
            values[plugin] = stanza._get_stanza_values()
        if self.iterables:
            iterables = []
            for stanza in self.iterables:
                iterables.append(stanza._get_stanza_values())
                iterables[-1].update({
                    '__childtag__': "{%s}%s" % (stanza.namespace,
                                                stanza.name)})
            values['substanzas'] = iterables
        return values

    def _set_stanza_values(self, values):
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
                                sub._set_stanza_values(subdict)
                                self.iterables.append(sub)
                                break
            elif interface in self.interfaces:
                self[interface] = value
            elif interface in self.plugin_attrib_map:
                if interface not in self.plugins:
                    self.init_plugin(interface)
                self.plugins[interface]._set_stanza_values(value)
        return self

    def __getitem__(self, attrib):
        """
        Return the value of a stanza interface using dictionary-like syntax.

        Example:
            >>> msg['body']
            'Message contents'

        Stanza interfaces are typically mapped directly to the underlying XML
        object, but can be overridden by the presence of a get_attrib method
        (or get_foo where the interface is named foo, etc).

        The search order for interface value retrieval for an interface
        named 'foo' is:
            1. The list of substanzas.
            2. The result of calling get_foo.
            3. The result of calling getFoo.
            4. The contents of the foo subelement, if foo is a sub interface.
            5. The value of the foo attribute of the XML object.
            6. The plugin named 'foo'
            7. An empty string.

        Arguments:
            attrib -- The name of the requested stanza interface.
        """
        if attrib == 'substanzas':
            return self.iterables
        elif attrib in self.interfaces:
            get_method = "get_%s" % attrib.lower()
            get_method2 = "get%s" % attrib.title()
            if hasattr(self, get_method):
                return getattr(self, get_method)()
            elif hasattr(self, get_method2):
                return getattr(self, get_method2)()
            else:
                if attrib in self.sub_interfaces:
                    return self._get_sub_text(attrib)
                else:
                    return self._get_attr(attrib)
        elif attrib in self.plugin_attrib_map:
            if attrib not in self.plugins:
                self.init_plugin(attrib)
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
        object, but can be overridden by the presence of a set_attrib method
        (or set_foo where the interface is named foo, etc).

        The effect of interface value assignment for an interface
        named 'foo' will be one of:
            1. Delete the interface's contents if the value is None.
            2. Call set_foo, if it exists.
            3. Call setFoo, if it exists.
            4. Set the text of a foo element, if foo is in sub_interfaces.
            5. Set the value of a top level XML attribute name foo.
            6. Attempt to pass value to a plugin named foo using the plugin's
               foo interface.
            7. Do nothing.

        Arguments:
            attrib -- The name of the stanza interface to modify.
            value  -- The new value of the stanza interface.
        """
        if attrib in self.interfaces:
            if value is not None:
                set_method = "set_%s" % attrib.lower()
                set_method2 = "set%s" % attrib.title()
                if hasattr(self, set_method):
                    getattr(self, set_method)(value,)
                elif hasattr(self, set_method2):
                    getattr(self, set_method2)(value,)
                else:
                    if attrib in self.sub_interfaces:
                        return self._set_sub_text(attrib, text=value)
                    else:
                        self._set_attr(attrib, value)
            else:
                self.__delitem__(attrib)
        elif attrib in self.plugin_attrib_map:
            if attrib not in self.plugins:
                self.init_plugin(attrib)
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
        object, but can be overridden by the presence of a del_attrib method
        (or del_foo where the interface is named foo, etc).

        The effect of deleting a stanza interface value named foo will be
        one of:
            1. Call del_foo, if it exists.
            2. Call delFoo, if it exists.
            3. Delete foo element, if foo is in sub_interfaces.
            4. Delete top level XML attribute named foo.
            5. Remove the foo plugin, if it was loaded.
            6. Do nothing.

        Arguments:
            attrib -- The name of the affected stanza interface.
        """
        if attrib in self.interfaces:
            del_method = "del_%s" % attrib.lower()
            del_method2 = "del%s" % attrib.title()
            if hasattr(self, del_method):
                getattr(self, del_method)()
            elif hasattr(self, del_method2):
                getattr(self, del_method2)()
            else:
                if attrib in self.sub_interfaces:
                    return self._del_sub(attrib)
                else:
                    self._del_attr(attrib)
        elif attrib in self.plugin_attrib_map:
            if attrib in self.plugins:
                xml = self.plugins[attrib].xml
                del self.plugins[attrib]
                self.xml.remove(xml)
        return self

    def _set_attr(self, name, value):
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

    def _del_attr(self, name):
        """
        Remove a top level attribute of the underlying XML object.

        Arguments:
            name -- The name of the attribute.
        """
        if name in self.xml.attrib:
            del self.xml.attrib[name]

    def _get_attr(self, name, default=''):
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

    def _get_sub_text(self, name, default=''):
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

    def _set_sub_text(self, name, text=None, keep=False):
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
        path = self._fix_ns(name, split=True)
        element = self.xml.find(name)

        if not text and not keep:
            return self._del_sub(name)

        if element is None:
            # We need to add the element. If the provided name was
            # an XPath expression, some of the intermediate elements
            # may already exist. If so, we want to use those instead
            # of generating new elements.
            last_xml = self.xml
            walked = []
            for ename in path:
                walked.append(ename)
                element = self.xml.find("/".join(walked))
                if element is None:
                    element = ET.Element(ename)
                    last_xml.append(element)
                last_xml = element
            element = last_xml

        element.text = text
        return element

    def _del_sub(self, name, all=False):
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
        path = self._fix_ns(name, split=True)
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
                    if element.tag == original_target or \
                        not element.getchildren():
                        # Only delete the originally requested elements, and
                        # any parent elements that have become empty.
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
            xpath = self._fix_ns(xpath, split=True, propagate_ns=False)

        # Extract the tag name and attribute checks for the first XPath node.
        components = xpath[0].split('@')
        tag = components[0]
        attributes = components[1:]

        if tag not in (self.name, "{%s}%s" % (self.namespace, self.name)) and \
            tag not in self.plugins and tag not in self.plugin_attrib:
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

        # Check sub interfaces.
        if len(xpath) > 1:
            next_tag = xpath[1]
            if next_tag in self.sub_interfaces and self[next_tag]:
                return True

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

    def _fix_ns(self, xpath, split=False, propagate_ns=True):
        """
        Apply the stanza's namespace to elements in an XPath expression.

        Arguments:
            xpath        -- The XPath expression to fix with namespaces.
            split        -- Indicates if the fixed XPath should be left as a
                            list of element names with namespaces. Defaults to
                            False, which returns a flat string path.
            propagate_ns -- Overrides propagating parent element namespaces
                            to child elements. Useful if you wish to simply
                            split an XPath that has non-specified namespaces,
                            and child and parent namespaces are known not to
                            always match. Defaults to True.
        """
        fixed = []
        # Split the XPath into a series of blocks, where a block
        # is started by an element with a namespace.
        ns_blocks = xpath.split('{')
        for ns_block in ns_blocks:
            if '}' in ns_block:
                # Apply the found namespace to following elements
                # that do not have namespaces.
                namespace = ns_block.split('}')[0]
                elements = ns_block.split('}')[1].split('/')
            else:
                # Apply the stanza's namespace to the following
                # elements since no namespace was provided.
                namespace = self.namespace
                elements = ns_block.split('/')

            for element in elements:
                if element:
                    # Skip empty entry artifacts from splitting.
                    if propagate_ns:
                        tag = '{%s}%s' % (namespace, element)
                    else:
                        tag = element
                    fixed.append(tag)
        if split:
            return fixed
        return '/'.join(fixed)

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
        values = self._get_stanza_values()
        for key in other.keys():
            if key not in values or values[key] != other[key]:
                return False

        # Check that the other stanza is a superset of this stanza.
        values = other._get_stanza_values()
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

    """
    StanzaBase provides the foundation for all other stanza objects used by
    SleekXMPP, and defines a basic set of interfaces common to nearly
    all stanzas. These interfaces are the 'id', 'type', 'to', and 'from'
    attributes. An additional interface, 'payload', is available to access
    the XML contents of the stanza. Most stanza objects will provided more
    specific interfaces, however.

    Stanza Interface:
        from    -- A JID object representing the sender's JID.
        id      -- An optional id value that can be used to associate stanzas
                   with their replies.
        payload -- The XML contents of the stanza.
        to      -- A JID object representing the recipient's JID.
        type    -- The type of stanza, typically will be 'normal', 'error',
                   'get', or 'set', etc.

    Attributes:
        stream -- The XMLStream instance that will handle sending this stanza.
        tag    -- The namespaced version of the stanza's name.

    Methods:
        set_type    -- Set the type of the stanza.
        get_to      -- Return the stanza recipients JID.
        set_to      -- Set the stanza recipient's JID.
        get_from    -- Return the stanza sender's JID.
        set_from    -- Set the stanza sender's JID.
        get_payload -- Return the stanza's XML contents.
        set_payload -- Append to the stanza's XML contents.
        del_payload -- Remove the stanza's XML contents.
        clear       -- Reset the stanza's XML contents.
        reply       -- Reset the stanza and modify the 'to' and 'from'
                       attributes to prepare for sending a reply.
        error       -- Set the stanza's type to 'error'.
        unhandled   -- Callback for when the stanza is not handled by a
                       stream handler.
        exception   -- Callback for if an exception is raised while
                       handling the stanza.
        send        -- Send the stanza using the stanza's stream.
    """

    name = 'stanza'
    namespace = 'jabber:client'
    interfaces = set(('type', 'to', 'from', 'id', 'payload'))
    types = set(('get', 'set', 'error', None, 'unavailable', 'normal', 'chat'))
    sub_interfaces = tuple()

    def __init__(self, stream=None, xml=None, stype=None,
                 sto=None, sfrom=None, sid=None):
        """
        Create a new stanza.

        Arguments:
            stream -- Optional XMLStream responsible for sending this stanza.
            xml    -- Optional XML contents to initialize stanza values.
            stype  -- Optional stanza type value.
            sto    -- Optional string or JID object of the recipient's JID.
            sfrom  -- Optional string or JID object of the sender's JID.
            sid    -- Optional ID value for the stanza.
        """
        # To comply with PEP8, method names now use underscores.
        # Deprecated method names are re-mapped for backwards compatibility.
        self.setType = self.set_type
        self.getTo = self.get_to
        self.setTo = self.set_to
        self.getFrom = self.get_from
        self.setFrom = self.set_from
        self.getPayload = self.get_payload
        self.setPayload = self.set_payload
        self.delPayload = self.del_payload

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

    def set_type(self, value):
        """
        Set the stanza's 'type' attribute.

        Only type values contained in StanzaBase.types are accepted.

        Arguments:
            value -- One of the values contained in StanzaBase.types
        """
        if value in self.types:
            self.xml.attrib['type'] = value
        return self

    def get_to(self):
        """Return the value of the stanza's 'to' attribute."""
        return JID(self._get_attr('to'))

    def set_to(self, value):
        """
        Set the 'to' attribute of the stanza.

        Arguments:
            value -- A string or JID object representing the recipient's JID.
        """
        return self._set_attr('to', str(value))

    def get_from(self):
        """Return the value of the stanza's 'from' attribute."""
        return JID(self._get_attr('from'))

    def set_from(self, value):
        """
        Set the 'from' attribute of the stanza.

        Arguments:
            from -- A string or JID object representing the sender's JID.
        """
        return self._set_attr('from', str(value))

    def get_payload(self):
        """Return a list of XML objects contained in the stanza."""
        return self.xml.getchildren()

    def set_payload(self, value):
        """
        Add XML content to the stanza.

        Arguments:
            value -- Either an XML or a stanza object, or a list
                     of XML or stanza objects.
        """
        if not isinstance(value, list):
            value = [value]
        for val in value:
            self.append(val)
        return self

    def del_payload(self):
        """Remove the XML contents of the stanza."""
        self.clear()
        return self

    def clear(self):
        """
        Remove all XML element contents and plugins.

        Any attribute values will be preserved.
        """
        for child in self.xml.getchildren():
            self.xml.remove(child)
        for plugin in list(self.plugins.keys()):
            del self.plugins[plugin]
        return self

    def reply(self):
        """
        Reset the stanza and swap its 'from' and 'to' attributes to prepare
        for sending a reply stanza.

        For client streams, the 'from' attribute is removed.
        """
        # if it's a component, use from
        if self.stream and hasattr(self.stream, "is_component") and \
            self.stream.is_component:
            self['from'], self['to'] = self['to'], self['from']
        else:
            self['to'] = self['from']
            del self['from']
        self.clear()
        return self

    def error(self):
        """Set the stanza's type to 'error'."""
        self['type'] = 'error'
        return self

    def unhandled(self):
        """
        Called when no handlers have been registered to process this
        stanza.

        Meant to be overridden.
        """
        pass

    def exception(self, e):
        """
        Handle exceptions raised during stanza processing.

        Meant to be overridden.
        """
        log.exception('Error handling {%s}%s stanza' % (self.namespace,
                                                            self.name))

    def send(self):
        """Queue the stanza to be sent on the XML stream."""
        self.stream.sendRaw(self.__str__())

    def __copy__(self):
        """
        Return a copy of the stanza object that does not share the
        same underlying XML object, but does share the same XML stream.
        """
        return self.__class__(xml=copy.deepcopy(self.xml),
                              stream=self.stream)

    def __str__(self):
        """Serialize the stanza's XML to a string."""
        return tostring(self.xml, xmlns='',
                        stanza_ns=self.namespace,
                        stream=self.stream)
