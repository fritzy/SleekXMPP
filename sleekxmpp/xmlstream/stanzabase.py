# -*- coding: utf-8 -*-
"""
    sleekxmpp.xmlstream.stanzabase
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements a wrapper layer for XML objects
    that allows them to be treated like dictionaries.

    Part of SleekXMPP: The Sleek XMPP Library

    :copyright: (c) 2011 Nathanael C. Fritz
    :license: MIT, see LICENSE for more details
"""

import copy
import logging
import sys
import weakref
from xml.etree import cElementTree as ET

from sleekxmpp.xmlstream import JID
from sleekxmpp.xmlstream.tostring import tostring
from sleekxmpp.thirdparty import OrderedDict


log = logging.getLogger(__name__)


# Used to check if an argument is an XML object.
XML_TYPE = type(ET.Element('xml'))


def register_stanza_plugin(stanza, plugin, iterable=False, overrides=False):
    """
    Associate a stanza object as a plugin for another stanza.

    >>> from sleekxmpp.xmlstream import register_stanza_plugin
    >>> register_stanza_plugin(Iq, CustomStanza)

    :param class stanza: The class of the parent stanza.
    :param class plugin: The class of the plugin stanza.
    :param bool iterable: Indicates if the plugin stanza should be
                          included in the parent stanza's iterable
                          ``'substanzas'`` interface results.
    :param bool overrides: Indicates if the plugin should be allowed
                           to override the interface handlers for
                           the parent stanza, based on the plugin's
                           ``overrides`` field.

    .. versionadded:: 1.0-Beta1
        Made ``register_stanza_plugin`` the default name. The prior
        ``registerStanzaPlugin`` function name remains as an alias.
    """
    tag = "{%s}%s" % (plugin.namespace, plugin.name)

    # Prevent weird memory reference gotchas by ensuring
    # that the parent stanza class has its own set of
    # plugin info maps and is not using the mappings from
    # an ancestor class (like ElementBase).
    plugin_info = ('plugin_attrib_map', 'plugin_tag_map',
                   'plugin_iterables', 'plugin_overrides')
    for attr in plugin_info:
        info = getattr(stanza, attr)
        setattr(stanza, attr, info.copy())

    stanza.plugin_attrib_map[plugin.plugin_attrib] = plugin
    stanza.plugin_tag_map[tag] = plugin

    if iterable:
        stanza.plugin_iterables.add(plugin)
    if overrides:
        for interface in plugin.overrides:
            stanza.plugin_overrides[interface] = plugin.plugin_attrib


# To maintain backwards compatibility for now, preserve the camel case name.
registerStanzaPlugin = register_stanza_plugin


class ElementBase(object):

    """
    The core of SleekXMPP's stanza XML manipulation and handling is provided
    by ElementBase. ElementBase wraps XML cElementTree objects and enables
    access to the XML contents through dictionary syntax, similar in style
    to the Ruby XMPP library Blather's stanza implementation.

    Stanzas are defined by their name, namespace, and interfaces. For
    example, a simplistic Message stanza could be defined as::

        >>> class Message(ElementBase):
        ...     name = "message"
        ...     namespace = "jabber:client"
        ...     interfaces = set(('to', 'from', 'type', 'body'))
        ...     sub_interfaces = set(('body',))

    The resulting Message stanza's contents may be accessed as so::

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
    is simply a stanza that has a plugin_attrib value. For example::

        >>> class MessagePlugin(ElementBase):
        ...     name = "custom_plugin"
        ...     namespace = "custom"
        ...     interfaces = set(('useful_thing', 'custom'))
        ...     plugin_attrib = "custom"

    The plugin stanza class must be associated with its intended
    container stanza by using register_stanza_plugin as so::

        >>> register_stanza_plugin(Message, MessagePlugin)

    The plugin may then be accessed as if it were built-in to the parent
    stanza::

        >>> message['custom']['useful_thing'] = 'foo'

    If a plugin provides an interface that is the same as the plugin's
    plugin_attrib value, then the plugin's interface may be assigned
    directly from the parent stanza, as shown below, but retrieving
    information will require all interfaces to be used, as so::

        >>> message['custom'] = 'bar' # Same as using message['custom']['custom']
        >>> message['custom']['custom'] # Must use all interfaces
        'bar'

    If the plugin sets :attr:`is_extension` to ``True``, then both setting
    and getting an interface value that is the same as the plugin's
    plugin_attrib value will work, as so::

        >>> message['custom'] = 'bar'  # Using is_extension=True
        >>> message['custom']
        'bar'


    :param xml: Initialize the stanza object with an existing XML object.
    :param parent: Optionally specify a parent stanza object will will
                   contain this substanza.
    """

    #: The XML tag name of the element, not including any namespace
    #: prefixes. For example, an :class:`ElementBase` object for ``<message />``
    #: would use ``name = 'message'``.
    name = 'stanza'

    #: The XML namespace for the element. Given ``<foo xmlns="bar" />``,
    #: then ``namespace = "bar"`` should be used. The default namespace
    #: is ``jabber:client`` since this is being used in an XMPP library.
    namespace = 'jabber:client'

    #: For :class:`ElementBase` subclasses which are intended to be used
    #: as plugins, the ``plugin_attrib`` value defines the plugin name.
    #: Plugins may be accessed by using the ``plugin_attrib`` value as
    #: the interface. An example using ``plugin_attrib = 'foo'``:
    #:
    #:     register_stanza_plugin(Message, FooPlugin)
    #:     msg = Message()
    #:     msg['foo']['an_interface_from_the_foo_plugin']
    plugin_attrib = 'plugin'

    #: The set of keys that the stanza provides for accessing and
    #: manipulating the underlying XML object. This set may be augmented
    #: with the :attr:`plugin_attrib` value of any registered
    #: stanza plugins.
    interfaces = set(('type', 'to', 'from', 'id', 'payload'))

    #: A subset of :attr:`interfaces` which maps interfaces to direct
    #: subelements of the underlying XML object. Using this set, the text
    #: of these subelements may be set, retrieved, or removed without
    #: needing to define custom methods.
    sub_interfaces = tuple()

    #: In some cases you may wish to override the behaviour of one of the
    #: parent stanza's interfaces. The ``overrides`` list specifies the
    #: interface name and access method to be overridden. For example,
    #: to override setting the parent's ``'condition'`` interface you
    #: would use::
    #:
    #:     overrides = ['set_condition']
    #:
    #: Getting and deleting the ``'condition'`` interface would not
    #: be affected.
    #:
    #: .. versionadded:: 1.0-Beta5
    overrides = []

    #: If you need to add a new interface to an existing stanza, you
    #: can create a plugin and set ``is_extension = True``. Be sure
    #: to set the :attr:`plugin_attrib` value to the desired interface
    #: name, and that it is the only interface listed in
    #: :attr:`interfaces`. Requests for the new interface from the
    #: parent stanza will be passed to the plugin directly.
    #:
    #: .. versionadded:: 1.0-Beta5
    is_extension = False

    #: A map of interface operations to the overriding functions.
    #: For example, after overriding the ``set`` operation for
    #: the interface ``body``, :attr:`plugin_overrides` would be::
    #:
    #:     {'set_body': <some function>}
    #:
    #: .. versionadded: 1.0-Beta5
    plugin_overrides = {}

    #: A mapping of the :attr:`plugin_attrib` values of registered
    #: plugins to their respective classes.
    plugin_attrib_map = {}

    #: A mapping of root element tag names (in ``'{namespace}elementname'``
    #: format) to the plugin classes responsible for them.
    plugin_tag_map = {}

    #: The set of stanza classes that can be iterated over using
    #: the 'substanzas' interface. Classes are added to this set
    #: when registering a plugin with ``iterable=True``::
    #:
    #:     register_stanza_plugin(DiscoInfo, DiscoItem, iterable=True)
    #:
    #: .. versionadded:: 1.0-Beta5
    plugin_iterables = set()

    #: A deprecated version of :attr:`plugin_iterables` that remains
    #: for backward compatibility. It required a parent stanza to
    #: know beforehand what stanza classes would be iterable::
    #:
    #:     class DiscoItem(ElementBase):
    #:         ...
    #:
    #:     class DiscoInfo(ElementBase):
    #:         subitem = (DiscoItem, )
    #:         ...
    #:
    #: .. deprecated:: 1.0-Beta5
    subitem = set()

    #: The default XML namespace: ``http://www.w3.org/XML/1998/namespace``.
    xml_ns = 'http://www.w3.org/XML/1998/namespace'

    def __init__(self, xml=None, parent=None):
        self._index = 0

        #: The underlying XML object for the stanza. It is a standard
        #: :class:`xml.etree.cElementTree` object.
        self.xml = xml

        #: An ordered dictionary of plugin stanzas, mapped by their
        #: :attr:`plugin_attrib` value.
        self.plugins = OrderedDict()

        #: A list of child stanzas whose class is included in
        #: :attr:`plugin_iterables`.
        self.iterables = []

        #: The name of the tag for the stanza's root element. It is the
        #: same as calling :meth:`tag_name()` and is formatted as
        #: ``'{namespace}elementname'``.
        self.tag = self.tag_name()

        #: A :class:`weakref.weakref` to the parent stanza, if there is one.
        #: If not, then :attr:`parent` is ``None``.
        self.parent = None
        if parent is not None:
            self.parent = weakref.ref(parent)

        if self.subitem is not None:
            for sub in self.subitem:
                self.plugin_iterables.add(sub)

        if self.setup(xml):
            # If we generated our own XML, then everything is ready.
            return

        # Initialize values using provided XML
        for child in self.xml.getchildren():
            if child.tag in self.plugin_tag_map:
                plugin_class = self.plugin_tag_map[child.tag]
                plugin = plugin_class(child, self)
                self.plugins[plugin.plugin_attrib] = plugin
                if plugin_class in self.plugin_iterables:
                    self.iterables.append(plugin)

    def setup(self, xml=None):
        """Initialize the stanza's XML contents.

        Will return ``True`` if XML was generated according to the stanza's
        definition instead of building a stanza object from an existing
        XML object.

        :param xml: An existing XML object to use for the stanza's content
                    instead of generating new XML.
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
        """Enable and initialize a stanza plugin.

        Alias for :meth:`init_plugin`.

        :param string attrib: The :attr:`plugin_attrib` value of the
                              plugin to enable.
        """
        return self.init_plugin(attrib)

    def init_plugin(self, attrib):
        """Enable and initialize a stanza plugin.

        :param string attrib: The :attr:`plugin_attrib` value of the
                              plugin to enable.
        """
        if attrib not in self.plugins:
            plugin_class = self.plugin_attrib_map[attrib]
            plugin = plugin_class(parent=self)
            self.plugins[attrib] = plugin
            if plugin_class in self.plugin_iterables:
                self.iterables.append(plugin)
        return self

    def _get_stanza_values(self):
        """Return A JSON/dictionary version of the XML content
        exposed through the stanza's interfaces::

            >>> msg = Message()
            >>> msg.values
            {'body': '', 'from': , 'mucnick': '', 'mucroom': '',
            'to': , 'type': 'normal', 'id': '', 'subject': ''}

        Likewise, assigning to :attr:`values` will change the XML
        content::

            >>> msg = Message()
            >>> msg.values = {'body': 'Hi!', 'to': 'user@example.com'}
            >>> msg
            '<message to="user@example.com"><body>Hi!</body></message>'

        .. versionadded:: 1.0-Beta1
        """
        values = {}
        for interface in self.interfaces:
            values[interface] = self[interface]
        for plugin, stanza in self.plugins.items():
            values[plugin] = stanza.values
        if self.iterables:
            iterables = []
            for stanza in self.iterables:
                iterables.append(stanza.values)
                iterables[-1]['__childtag__'] = stanza.tag
            values['substanzas'] = iterables
        return values

    def _set_stanza_values(self, values):
        """Set multiple stanza interface values using a dictionary.

        Stanza plugin values may be set using nested dictionaries.

        :param values: A dictionary mapping stanza interface with values.
                       Plugin interfaces may accept a nested dictionary that
                       will be used recursively.

        .. versionadded:: 1.0-Beta1
        """
        iterable_interfaces = [p.plugin_attrib for \
                                    p in self.plugin_iterables]

        for interface, value in values.items():
            if interface == 'substanzas':
                # Remove existing substanzas
                for stanza in self.iterables:
                    self.xml.remove(stanza.xml)
                self.iterables = []

                # Add new substanzas
                for subdict in value:
                    if '__childtag__' in subdict:
                        for subclass in self.plugin_iterables:
                            child_tag = "{%s}%s" % (subclass.namespace,
                                                    subclass.name)
                            if subdict['__childtag__'] == child_tag:
                                sub = subclass(parent=self)
                                sub.values = subdict
                                self.iterables.append(sub)
                                break
            elif interface in self.interfaces:
                self[interface] = value
            elif interface in self.plugin_attrib_map:
                if interface not in iterable_interfaces:
                    if interface not in self.plugins:
                        self.init_plugin(interface)
                    self.plugins[interface].values = value
        return self

    def __getitem__(self, attrib):
        """Return the value of a stanza interface using dict-like syntax.

        Example::

            >>> msg['body']
            'Message contents'

        Stanza interfaces are typically mapped directly to the underlying XML
        object, but can be overridden by the presence of a ``get_attrib``
        method (or ``get_foo`` where the interface is named ``'foo'``, etc).

        The search order for interface value retrieval for an interface
        named ``'foo'`` is:

            1. The list of substanzas (``'substanzas'``)
            2. The result of calling the ``get_foo`` override handler.
            3. The result of calling ``get_foo``.
            4. The result of calling ``getFoo``.
            5. The contents of the ``foo`` subelement, if ``foo`` is listed
               in :attr:`sub_interfaces`.
            6. The value of the ``foo`` attribute of the XML object.
            7. The plugin named ``'foo'``
            8. An empty string.

        :param string attrib: The name of the requested stanza interface.
        """
        if attrib == 'substanzas':
            return self.iterables
        elif attrib in self.interfaces:
            get_method = "get_%s" % attrib.lower()
            get_method2 = "get%s" % attrib.title()

            if self.plugin_overrides:
                plugin = self.plugin_overrides.get(get_method, None)
                if plugin:
                    if plugin not in self.plugins:
                        self.init_plugin(plugin)
                    handler = getattr(self.plugins[plugin], get_method, None)
                    if handler:
                        return handler()

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
            if self.plugins[attrib].is_extension:
                return self.plugins[attrib][attrib]
            return self.plugins[attrib]
        else:
            return ''

    def __setitem__(self, attrib, value):
        """Set the value of a stanza interface using dictionary-like syntax.

        Example::

            >>> msg['body'] = "Hi!"
            >>> msg['body']
            'Hi!'

        Stanza interfaces are typically mapped directly to the underlying XML
        object, but can be overridden by the presence of a ``set_attrib``
        method (or ``set_foo`` where the interface is named ``'foo'``, etc).

        The effect of interface value assignment for an interface
        named ``'foo'`` will be one of:

            1. Delete the interface's contents if the value is None.
            2. Call the ``set_foo`` override handler, if it exists.
            3. Call ``set_foo``, if it exists.
            4. Call ``setFoo``, if it exists.
            5. Set the text of a ``foo`` element, if ``'foo'`` is
               in :attr:`sub_interfaces`.
            6. Set the value of a top level XML attribute named ``foo``.
            7. Attempt to pass the value to a plugin named ``'foo'`` using
               the plugin's ``'foo'`` interface.
            8. Do nothing.

        :param string attrib: The name of the stanza interface to modify.
        :param value: The new value of the stanza interface.
        """
        if attrib in self.interfaces:
            if value is not None:
                set_method = "set_%s" % attrib.lower()
                set_method2 = "set%s" % attrib.title()

                if self.plugin_overrides:
                    plugin = self.plugin_overrides.get(set_method, None)
                    if plugin:
                        if plugin not in self.plugins:
                            self.init_plugin(plugin)
                        handler = getattr(self.plugins[plugin],
                                          set_method, None)
                        if handler:
                            return handler(value)

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
        """Delete the value of a stanza interface using dict-like syntax.

        Example::

            >>> msg['body'] = "Hi!"
            >>> msg['body']
            'Hi!'
            >>> del msg['body']
            >>> msg['body']
            ''

        Stanza interfaces are typically mapped directly to the underlyig XML
        object, but can be overridden by the presence of a ``del_attrib``
        method (or ``del_foo`` where the interface is named ``'foo'``, etc).

        The effect of deleting a stanza interface value named ``foo`` will be
        one of:

            1. Call ``del_foo`` override handler, if it exists.
            2. Call ``del_foo``, if it exists.
            3. Call ``delFoo``, if it exists.
            4. Delete ``foo`` element, if ``'foo'`` is in
               :attr:`sub_interfaces`.
            5. Delete top level XML attribute named ``foo``.
            6. Remove the ``foo`` plugin, if it was loaded.
            7. Do nothing.

        :param attrib: The name of the affected stanza interface.
        """
        if attrib in self.interfaces:
            del_method = "del_%s" % attrib.lower()
            del_method2 = "del%s" % attrib.title()

            if self.plugin_overrides:
                plugin = self.plugin_overrides.get(del_method, None)
                if plugin:
                    if plugin not in self.plugins:
                        self.init_plugin(plugin)
                    handler = getattr(self.plugins[plugin], del_method, None)
                    if handler:
                        return handler()

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
                if self.plugins[attrib].is_extension:
                    del self.plugins[attrib][attrib]
                del self.plugins[attrib]
                try:
                    self.xml.remove(xml)
                except:
                    pass
        return self

    def _set_attr(self, name, value):
        """Set the value of a top level attribute of the XML object.

        If the new value is None or an empty string, then the attribute will
        be removed.

        :param name: The name of the attribute.
        :param value: The new value of the attribute, or None or '' to
                      remove it.
        """
        if value is None or value == '':
            self.__delitem__(name)
        else:
            self.xml.attrib[name] = value

    def _del_attr(self, name):
        """Remove a top level attribute of the XML object.

        :param name: The name of the attribute.
        """
        if name in self.xml.attrib:
            del self.xml.attrib[name]

    def _get_attr(self, name, default=''):
        """Return the value of a top level attribute of the XML object.

        In case the attribute has not been set, a default value can be
        returned instead. An empty string is returned if no other default
        is supplied.

        :param name: The name of the attribute.
        :param default: Optional value to return if the attribute has not
                        been set. An empty string is returned otherwise.
        """
        return self.xml.attrib.get(name, default)

    def _get_sub_text(self, name, default=''):
        """Return the text contents of a sub element.

        In case the element does not exist, or it has no textual content,
        a default value can be returned instead. An empty string is returned
        if no other default is supplied.

        :param name: The name or XPath expression of the element.
        :param default: Optional default to return if the element does
                        not exists. An empty string is returned otherwise.
        """
        name = self._fix_ns(name)
        stanza = self.xml.find(name)
        if stanza is None or stanza.text is None:
            return default
        else:
            return stanza.text

    def _set_sub_text(self, name, text=None, keep=False):
        """Set the text contents of a sub element.

        In case the element does not exist, a element will be created,
        and its text contents will be set.

        If the text is set to an empty string, or None, then the
        element will be removed, unless keep is set to True.

        :param name: The name or XPath expression of the element.
        :param text: The new textual content of the element. If the text
                     is an empty string or None, the element will be removed
                     unless the parameter keep is True.
        :param keep: Indicates if the element should be kept if its text is
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
        """Remove sub elements that match the given name or XPath.

        If the element is in a path, then any parent elements that become
        empty after deleting the element may also be deleted if requested
        by setting all=True.

        :param name: The name or XPath expression for the element(s) to remove.
        :param bool all: If True, remove all empty elements in the path to the
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
        """Compare a stanza object with an XPath-like expression.

        If the XPath matches the contents of the stanza object, the match
        is successful.

        The XPath expression may include checks for stanza attributes.
        For example::

            'presence@show=xa@priority=2/status'

        Would match a presence stanza whose show value is set to ``'xa'``,
        has a priority value of ``'2'``, and has a status element.

        :param string xpath: The XPath expression to check against. It
                             may be either a string or a list of element
                             names with attribute checks.
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
        """Find an XML object in this stanza given an XPath expression.

        Exposes ElementTree interface for backwards compatibility.

        .. note::

            Matching on attribute values is not supported in Python 2.6
            or Python 3.1

        :param string xpath: An XPath expression matching a single
                             desired element.
        """
        return self.xml.find(xpath)

    def findall(self, xpath):
        """Find multiple XML objects in this stanza given an XPath expression.

        Exposes ElementTree interface for backwards compatibility.

        .. note::

            Matching on attribute values is not supported in Python 2.6
            or Python 3.1.

        :param string xpath: An XPath expression matching multiple
                             desired elements.
        """
        return self.xml.findall(xpath)

    def get(self, key, default=None):
        """Return the value of a stanza interface.

        If the found value is None or an empty string, return the supplied
        default value.

        Allows stanza objects to be used like dictionaries.

        :param string key: The name of the stanza interface to check.
        :param default: Value to return if the stanza interface has a value
                        of ``None`` or ``""``. Will default to returning None.
        """
        value = self[key]
        if value is None or value == '':
            return default
        return value

    def keys(self):
        """Return the names of all stanza interfaces provided by the
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
        """Append either an XML object or a substanza to this stanza object.

        If a substanza object is appended, it will be added to the list
        of iterable stanzas.

        Allows stanza objects to be used like lists.

        :param item: Either an XML object or a stanza object to add to
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
        """Append an XML object to the stanza's XML.

        The added XML will not be included in the list of
        iterable substanzas.

        :param XML xml: The XML object to add to the stanza.
        """
        self.xml.append(xml)
        return self

    def pop(self, index=0):
        """Remove and return the last substanza in the list of
        iterable substanzas.

        Allows stanza objects to be used like lists.

        :param int index: The index of the substanza to remove.
        """
        substanza = self.iterables.pop(index)
        self.xml.remove(substanza.xml)
        return substanza

    def next(self):
        """Return the next iterable substanza."""
        return self.__next__()

    def clear(self):
        """Remove all XML element contents and plugins.

        Any attribute values will be preserved.
        """
        for child in self.xml.getchildren():
            self.xml.remove(child)
        for plugin in list(self.plugins.keys()):
            del self.plugins[plugin]
        return self

    @classmethod
    def tag_name(cls):
        """Return the namespaced name of the stanza's root element.

        The format for the tag name is::

            '{namespace}elementname'

        For example, for the stanza ``<foo xmlns="bar" />``,
        ``stanza.tag_name()`` would return ``"{bar}foo"``.
        """
        return "{%s}%s" % (cls.namespace, cls.name)

    @property
    def attrib(self):
        """Return the stanza object itself.

        Older implementations of stanza objects used XML objects directly,
        requiring the use of ``.attrib`` to access attribute values.

        Use of the dictionary syntax with the stanza object itself for
        accessing stanza interfaces is preferred.

        .. deprecated:: 1.0
        """
        return self

    def _fix_ns(self, xpath, split=False, propagate_ns=True):
        """Apply the stanza's namespace to elements in an XPath expression.

        :param string xpath: The XPath expression to fix with namespaces.
        :param bool split: Indicates if the fixed XPath should be left as a
                           list of element names with namespaces. Defaults to
                           False, which returns a flat string path.
        :param bool propagate_ns: Overrides propagating parent element
                                  namespaces to child elements. Useful if
                                  you wish to simply split an XPath that has
                                  non-specified namespaces, and child and
                                  parent namespaces are known not to always
                                  match. Defaults to True.
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
        """Compare the stanza object with another to test for equality.

        Stanzas are equal if their interfaces return the same values,
        and if they are both instances of ElementBase.

        :param ElementBase other: The stanza object to compare against.
        """
        if not isinstance(other, ElementBase):
            return False

        # Check that this stanza is a superset of the other stanza.
        values = self.values
        for key in other.keys():
            if key not in values or values[key] != other[key]:
                return False

        # Check that the other stanza is a superset of this stanza.
        values = other.values
        for key in self.keys():
            if key not in values or values[key] != self[key]:
                return False

        # Both stanzas are supersets of each other, therefore they
        # must be equal.
        return True

    def __ne__(self, other):
        """Compare the stanza object with another to test for inequality.

        Stanzas are not equal if their interfaces return different values,
        or if they are not both instances of ElementBase.

        :param ElementBase other: The stanza object to compare against.
        """
        return not self.__eq__(other)

    def __bool__(self):
        """Stanza objects should be treated as True in boolean contexts.

        Python 3.x version.
        """
        return True

    def __nonzero__(self):
        """Stanza objects should be treated as True in boolean contexts.

        Python 2.x version.
        """
        return True

    def __len__(self):
        """Return the number of iterable substanzas in this stanza."""
        return len(self.iterables)

    def __iter__(self):
        """Return an iterator object for the stanza's substanzas.

        The iterator is the stanza object itself. Attempting to use two
        iterators on the same stanza at the same time is discouraged.
        """
        self._index = 0
        return self

    def __next__(self):
        """Return the next iterable substanza."""
        self._index += 1
        if self._index > len(self.iterables):
            self._index = 0
            raise StopIteration
        return self.iterables[self._index - 1]

    def __copy__(self):
        """Return a copy of the stanza object that does not share the same
        underlying XML object.
        """
        return self.__class__(xml=copy.deepcopy(self.xml), parent=self.parent)

    def __str__(self, top_level_ns=True):
        """Return a string serialization of the underlying XML object.

        .. seealso:: :ref:`tostring`

        :param bool top_level_ns: Display the top-most namespace.
                                  Defaults to True.
        """
        stanza_ns = '' if top_level_ns else self.namespace
        return tostring(self.xml, xmlns='',
                        stanza_ns=stanza_ns,
                        top_level=not top_level_ns)

    def __repr__(self):
        """Use the stanza's serialized XML as its representation."""
        return self.__str__()


class StanzaBase(ElementBase):

    """
    StanzaBase provides the foundation for all other stanza objects used
    by SleekXMPP, and defines a basic set of interfaces common to nearly
    all stanzas. These interfaces are the ``'id'``, ``'type'``, ``'to'``,
    and ``'from'`` attributes. An additional interface, ``'payload'``, is
    available to access the XML contents of the stanza. Most stanza objects
    will provided more specific interfaces, however.

    **Stanza Interfaces:**

        :id: An optional id value that can be used to associate stanzas
        :to: A JID object representing the recipient's JID.
        :from: A JID object representing the sender's JID.
               with their replies.
        :type: The type of stanza, typically will be ``'normal'``,
               ``'error'``, ``'get'``, or ``'set'``, etc.
        :payload: The XML contents of the stanza.

    :param XMLStream stream: Optional :class:`sleekxmpp.xmlstream.XMLStream`
                             object responsible for sending this stanza.
    :param XML xml: Optional XML contents to initialize stanza values.
    :param string stype: Optional stanza type value.
    :param sto: Optional string or :class:`sleekxmpp.xmlstream.JID`
                object of the recipient's JID.
    :param sfrom: Optional string or :class:`sleekxmpp.xmlstream.JID`
                  object of the sender's JID.
    :param string sid: Optional ID value for the stanza.
    """

    #: The default XMPP client namespace
    namespace = 'jabber:client'

    #: There is a small set of attributes which apply to all XMPP stanzas:
    #: the stanza type, the to and from JIDs, the stanza ID, and, especially
    #: in the case of an Iq stanza, a payload.
    interfaces = set(('type', 'to', 'from', 'id', 'payload'))

    #: A basic set of allowed values for the ``'type'`` interface.
    types = set(('get', 'set', 'error', None, 'unavailable', 'normal', 'chat'))

    def __init__(self, stream=None, xml=None, stype=None,
                 sto=None, sfrom=None, sid=None):
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
        """Set the stanza's ``'type'`` attribute.

        Only type values contained in :attr:`types` are accepted.

        :param string value: One of the values contained in :attr:`types`
        """
        if value in self.types:
            self.xml.attrib['type'] = value
        return self

    def get_to(self):
        """Return the value of the stanza's ``'to'`` attribute."""
        return JID(self._get_attr('to'))

    def set_to(self, value):
        """Set the ``'to'`` attribute of the stanza.

        :param value: A string or :class:`sleekxmpp.xmlstream.JID` object
               representing the recipient's JID.
        """
        return self._set_attr('to', str(value))

    def get_from(self):
        """Return the value of the stanza's ``'from'`` attribute."""
        return JID(self._get_attr('from'))

    def set_from(self, value):
        """Set the 'from' attribute of the stanza.

        Arguments:
            from -- A string or JID object representing the sender's JID.
        """
        return self._set_attr('from', str(value))

    def get_payload(self):
        """Return a list of XML objects contained in the stanza."""
        return self.xml.getchildren()

    def set_payload(self, value):
        """Add XML content to the stanza.

        :param value: Either an XML or a stanza object, or a list
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

    def reply(self, clear=True):
        """Prepare the stanza for sending a reply.

        Swaps the ``'from'`` and ``'to'`` attributes.

        If ``clear=True``, then also remove the stanza's
        contents to make room for the reply content.

        For client streams, the ``'from'`` attribute is removed.

        :param bool clear: Indicates if the stanza's contents should be
                           removed. Defaults to ``True``.
        """
        # if it's a component, use from
        if self.stream and hasattr(self.stream, "is_component") and \
            self.stream.is_component:
            self['from'], self['to'] = self['to'], self['from']
        else:
            self['to'] = self['from']
            del self['from']
        if clear:
            self.clear()
        return self

    def error(self):
        """Set the stanza's type to ``'error'``."""
        self['type'] = 'error'
        return self

    def unhandled(self):
        """Called if no handlers have been registered to process this stanza.

        Meant to be overridden.
        """
        pass

    def exception(self, e):
        """Handle exceptions raised during stanza processing.

        Meant to be overridden.
        """
        log.exception('Error handling {%s}%s stanza', self.namespace,
                                                      self.name)

    def send(self, now=False):
        """Queue the stanza to be sent on the XML stream.

        :param bool now: Indicates if the queue should be skipped and the
                         stanza sent immediately. Useful for stream
                         initialization. Defaults to ``False``.
        """
        self.stream.send_raw(self.__str__(), now=now)

    def __copy__(self):
        """Return a copy of the stanza object that does not share the
        same underlying XML object, but does share the same XML stream.
        """
        return self.__class__(xml=copy.deepcopy(self.xml),
                              stream=self.stream)

    def __str__(self, top_level_ns=False):
        """Serialize the stanza's XML to a string.

        :param bool top_level_ns: Display the top-most namespace.
                                  Defaults to ``False``.
        """
        stanza_ns = '' if top_level_ns else self.namespace
        return tostring(self.xml, xmlns='',
                        stanza_ns=stanza_ns,
                        stream=self.stream,
                        top_level=not top_level_ns)


#: A JSON/dictionary version of the XML content exposed through
#: the stanza interfaces::
#:
#:     >>> msg = Message()
#:     >>> msg.values
#:    {'body': '', 'from': , 'mucnick': '', 'mucroom': '',
#:     'to': , 'type': 'normal', 'id': '', 'subject': ''}
#:
#: Likewise, assigning to the :attr:`values` will change the XML
#: content::
#:
#:     >>> msg = Message()
#:     >>> msg.values = {'body': 'Hi!', 'to': 'user@example.com'}
#:     >>> msg
#:     '<message to="user@example.com"><body>Hi!</body></message>'
#:
#: Child stanzas are exposed as nested dictionaries.
ElementBase.values = property(ElementBase._get_stanza_values,
                              ElementBase._set_stanza_values)


# To comply with PEP8, method names now use underscores.
# Deprecated method names are re-mapped for backwards compatibility.
ElementBase.initPlugin = ElementBase.init_plugin
ElementBase._getAttr = ElementBase._get_attr
ElementBase._setAttr = ElementBase._set_attr
ElementBase._delAttr = ElementBase._del_attr
ElementBase._getSubText = ElementBase._get_sub_text
ElementBase._setSubText = ElementBase._set_sub_text
ElementBase._delSub = ElementBase._del_sub
ElementBase.getStanzaValues = ElementBase._get_stanza_values
ElementBase.setStanzaValues = ElementBase._set_stanza_values

StanzaBase.setType = StanzaBase.set_type
StanzaBase.getTo = StanzaBase.get_to
StanzaBase.setTo = StanzaBase.set_to
StanzaBase.getFrom = StanzaBase.get_from
StanzaBase.setFrom = StanzaBase.set_from
StanzaBase.getPayload = StanzaBase.get_payload
StanzaBase.setPayload = StanzaBase.set_payload
StanzaBase.delPayload = StanzaBase.del_payload
