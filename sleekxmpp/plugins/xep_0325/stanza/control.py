"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Sustainable Innovation, Joachim.lindborg@sust.se, bjorn.westrom@consoden.se
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp import Iq, Message
from sleekxmpp.xmlstream import register_stanza_plugin, ElementBase, ET, JID
from re import match

class Control(ElementBase):
    """ Placeholder for the namespace, not used as a stanza """
    namespace = 'urn:xmpp:iot:control'
    name = 'control'
    plugin_attrib = name
    interfaces = set(tuple())

class ControlSet(ElementBase):
    namespace = 'urn:xmpp:iot:control'
    name = 'set'
    plugin_attrib = name
    interfaces = set(['nodes','datas'])

    def __init__(self, xml=None, parent=None):
        ElementBase.__init__(self, xml, parent)
        self._nodes = set()
        self._datas = set()

    def setup(self, xml=None):
        """
        Populate the stanza object using an optional XML object.

        Overrides ElementBase.setup

        Caches item information.

        Arguments:
            xml -- Use an existing XML object for the stanza's values.
        """
        ElementBase.setup(self, xml)
        self._nodes = set([node['nodeId'] for node in self['nodes']])
        self._datas = set([data['name'] for data in self['datas']])

    def add_node(self, nodeId, sourceId=None, cacheType=None):
        """
        Add a new node element. Each item is required to have a
        nodeId, but may also specify a sourceId value and cacheType.

        Arguments:
            nodeId    -- The ID for the node.
            sourceId  -- [optional] identifying the data source controlling the device
            cacheType -- [optional] narrowing down the search to a specific kind of node
        """
        if nodeId not in self._nodes:
            self._nodes.add((nodeId))
            node = RequestNode(parent=self)
            node['nodeId'] = nodeId
            node['sourceId'] = sourceId
            node['cacheType'] = cacheType
            self.iterables.append(node)
            return node
        return None

    def del_node(self, nodeId):
        """
        Remove a single node.

        Arguments:
            nodeId  -- Node ID of the item to remove.
        """
        if nodeId in self._nodes:
            nodes = [i for i in self.iterables if isinstance(i, RequestNode)]
            for node in nodes:
                if node['nodeId'] == nodeId:
                    self.xml.remove(node.xml)
                    self.iterables.remove(node)
                    return True
        return False

    def get_nodes(self):
        """Return all nodes."""
        nodes = []
        for node in self['substanzas']:
            if isinstance(node, RequestNode):
                nodes.append(node)
        return nodes

    def set_nodes(self, nodes):
        """
        Set or replace all nodes. The given nodes must be in a
        list or set where each item is a tuple of the form:
            (nodeId, sourceId, cacheType)

        Arguments:
            nodes -- A series of nodes in tuple format.
        """
        self.del_nodes()
        for node in nodes:
            if isinstance(node, RequestNode):
                self.add_node(node['nodeId'], node['sourceId'], node['cacheType'])
            else:
                nodeId, sourceId, cacheType = node
                self.add_node(nodeId, sourceId, cacheType)

    def del_nodes(self):
        """Remove all nodes."""
        self._nodes = set()
        nodes = [i for i in self.iterables if isinstance(i, RequestNode)]
        for node in nodes:
            self.xml.remove(node.xml)
            self.iterables.remove(node)


    def add_data(self, name, typename, value):
        """
        Add a new data element.

        Arguments:
            name       -- The name of the data element
            typename   -- The type of data element
                          (boolean, color, string, date, dateTime,
                           double, duration, int, long, time)
            value      -- The value of the data element
        """
        if name not in self._datas:
            dataObj = None
            if typename == "boolean":
                dataObj = BooleanParameter(parent=self)
            elif typename == "color":
                dataObj = ColorParameter(parent=self)
            elif typename == "string":
                dataObj = StringParameter(parent=self)
            elif typename == "date":
                dataObj = DateParameter(parent=self)
            elif typename == "dateTime":
                dataObj = DateTimeParameter(parent=self)
            elif typename == "double":
                dataObj = DoubleParameter(parent=self)
            elif typename == "duration":
                dataObj = DurationParameter(parent=self)
            elif typename == "int":
                dataObj = IntParameter(parent=self)
            elif typename == "long":
                dataObj = LongParameter(parent=self)
            elif typename == "time":
                dataObj = TimeParameter(parent=self)

            dataObj['name'] = name
            dataObj['value'] = value

            self._datas.add(name)
            self.iterables.append(dataObj)
            return dataObj
        return None

    def del_data(self, name):
        """
        Remove a single data element.

        Arguments:
            data_name  -- The data element name to remove.
        """
        if name in self._datas:
            datas = [i for i in self.iterables if isinstance(i, BaseParameter)]
            for data in datas:
                if data['name'] == name:
                    self.xml.remove(data.xml)
                    self.iterables.remove(data)
                    return True
        return False

    def get_datas(self):
        """ Return all data elements. """
        datas = []
        for data in self['substanzas']:
            if isinstance(data, BaseParameter):
                datas.append(data)
        return datas

    def set_datas(self, datas):
        """
        Set or replace all data elements. The given elements must be in a
        list or set where each item is a data element (numeric, string, boolean, dateTime, timeSpan or enum)

        Arguments:
            datas -- A series of data elements.
        """
        self.del_datas()
        for data in datas:
            self.add_data(name=data['name'], typename=data._get_typename(), value=data['value'])

    def del_datas(self):
        """Remove all data elements."""
        self._datas = set()
        datas = [i for i in self.iterables if isinstance(i, BaseParameter)]
        for data in datas:
            self.xml.remove(data.xml)
            self.iterables.remove(data)


class RequestNode(ElementBase):
    """ Node element in a request """
    namespace = 'urn:xmpp:iot:control'
    name = 'node'
    plugin_attrib = name
    interfaces = set(['nodeId','sourceId','cacheType'])


class ControlSetResponse(ElementBase):
    namespace = 'urn:xmpp:iot:control'
    name = 'setResponse'
    plugin_attrib = name
    interfaces = set(['responseCode'])

    def __init__(self, xml=None, parent=None):
        ElementBase.__init__(self, xml, parent)
        self._nodes = set()
        self._datas = set()

    def setup(self, xml=None):
        """
        Populate the stanza object using an optional XML object.

        Overrides ElementBase.setup

        Caches item information.

        Arguments:
            xml -- Use an existing XML object for the stanza's values.
        """
        ElementBase.setup(self, xml)
        self._nodes = set([node['nodeId'] for node in self['nodes']])
        self._datas = set([data['name'] for data in self['datas']])

    def add_node(self, nodeId, sourceId=None, cacheType=None):
        """
        Add a new node element. Each item is required to have a
        nodeId, but may also specify a sourceId value and cacheType.

        Arguments:
            nodeId    -- The ID for the node.
            sourceId  -- [optional] identifying the data source controlling the device
            cacheType -- [optional] narrowing down the search to a specific kind of node
        """
        if nodeId not in self._nodes:
            self._nodes.add(nodeId)
            node = RequestNode(parent=self)
            node['nodeId'] = nodeId
            node['sourceId'] = sourceId
            node['cacheType'] = cacheType
            self.iterables.append(node)
            return node
        return None

    def del_node(self, nodeId):
        """
        Remove a single node.

        Arguments:
            nodeId  -- Node ID of the item to remove.
        """
        if nodeId in self._nodes:
            nodes = [i for i in self.iterables if isinstance(i, RequestNode)]
            for node in nodes:
                if node['nodeId'] == nodeId:
                    self.xml.remove(node.xml)
                    self.iterables.remove(node)
                    return True
        return False

    def get_nodes(self):
        """Return all nodes."""
        nodes = []
        for node in self['substanzas']:
            if isinstance(node, RequestNode):
                nodes.append(node)
        return nodes

    def set_nodes(self, nodes):
        """
        Set or replace all nodes. The given nodes must be in a
        list or set where each item is a tuple of the form:
            (nodeId, sourceId, cacheType)

        Arguments:
            nodes -- A series of nodes in tuple format.
        """
        self.del_nodes()
        for node in nodes:
            if isinstance(node, RequestNode):
                self.add_node(node['nodeId'], node['sourceId'], node['cacheType'])
            else:
                nodeId, sourceId, cacheType = node
                self.add_node(nodeId, sourceId, cacheType)

    def del_nodes(self):
        """Remove all nodes."""
        self._nodes = set()
        nodes = [i for i in self.iterables if isinstance(i, RequestNode)]
        for node in nodes:
            self.xml.remove(node.xml)
            self.iterables.remove(node)


    def add_data(self, name):
        """
        Add a new ResponseParameter element.

        Arguments:
            name   -- Name of the parameter
        """
        if name not in self._datas:
            self._datas.add(name)
            data = ResponseParameter(parent=self)
            data['name'] = name
            self.iterables.append(data)
            return data
        return None

    def del_data(self, name):
        """
        Remove a single ResponseParameter element.

        Arguments:
            name  -- The data element name to remove.
        """
        if name in self._datas:
            datas = [i for i in self.iterables if isinstance(i, ResponseParameter)]
            for data in datas:
                if data['name'] == name:
                    self.xml.remove(data.xml)
                    self.iterables.remove(data)
                    return True
        return False

    def get_datas(self):
        """ Return all ResponseParameter elements. """
        datas = set()
        for data in self['substanzas']:
            if isinstance(data, ResponseParameter):
                datas.add(data)
        return datas

    def set_datas(self, datas):
        """
        Set or replace all data elements. The given elements must be in a
        list or set of ResponseParameter elements

        Arguments:
            datas -- A series of data element names.
        """
        self.del_datas()
        for data in datas:
            self.add_data(name=data['name'])

    def del_datas(self):
        """Remove all ResponseParameter elements."""
        self._datas = set()
        datas = [i for i in self.iterables if isinstance(i, ResponseParameter)]
        for data in datas:
            self.xml.remove(data.xml)
            self.iterables.remove(data)


class Error(ElementBase):
    namespace = 'urn:xmpp:iot:control'
    name = 'error'
    plugin_attrib = name
    interfaces = set(['var','text'])

    def get_text(self):
        """Return then contents inside the XML tag."""
        return self.xml.text

    def set_text(self, value):
        """Set then contents inside the XML tag.

        Arguments:
            value -- string
        """

        self.xml.text = value
        return self

    def del_text(self):
        """Remove the contents inside the XML tag."""
        self.xml.text = ""
        return self

class ResponseParameter(ElementBase):
    """
    Parameter element in ControlSetResponse.
    """
    namespace = 'urn:xmpp:iot:control'
    name = 'parameter'
    plugin_attrib = name
    interfaces = set(['name'])


class BaseParameter(ElementBase):
    """
    Parameter element in SetCommand. This is a base class,
    all instances of parameters added to SetCommand must be of types:
        BooleanParameter
        ColorParameter
        StringParameter
        DateParameter
        DateTimeParameter
        DoubleParameter
        DurationParameter
        IntParameter
        LongParameter
        TimeParameter
    """
    namespace = 'urn:xmpp:iot:control'
    name = 'baseParameter'
    plugin_attrib = name
    interfaces = set(['name','value'])

    def _get_typename(self):
        return self.name


class BooleanParameter(BaseParameter):
    """
    Field data of type boolean.
    Note that the value is expressed as a string.
    """
    name = 'boolean'
    plugin_attrib = name

class ColorParameter(BaseParameter):
    """
    Field data of type color.
    Note that the value is expressed as a string.
    """
    name = 'color'
    plugin_attrib = name

class StringParameter(BaseParameter):
    """
    Field data of type string.
    """
    name = 'string'
    plugin_attrib = name

class DateParameter(BaseParameter):
    """
    Field data of type date.
    Note that the value is expressed as a string.
    """
    name = 'date'
    plugin_attrib = name

class DateTimeParameter(BaseParameter):
    """
    Field data of type dateTime.
    Note that the value is expressed as a string.
    """
    name = 'dateTime'
    plugin_attrib = name

class DoubleParameter(BaseParameter):
    """
    Field data of type double.
    Note that the value is expressed as a string.
    """
    name = 'double'
    plugin_attrib = name

class DurationParameter(BaseParameter):
    """
    Field data of type duration.
    Note that the value is expressed as a string.
    """
    name = 'duration'
    plugin_attrib = name

class IntParameter(BaseParameter):
    """
    Field data of type int.
    Note that the value is expressed as a string.
    """
    name = 'int'
    plugin_attrib = name

class LongParameter(BaseParameter):
    """
    Field data of type long (64-bit int).
    Note that the value is expressed as a string.
    """
    name = 'long'
    plugin_attrib = name

class TimeParameter(BaseParameter):
    """
    Field data of type time.
    Note that the value is expressed as a string.
    """
    name = 'time'
    plugin_attrib = name

register_stanza_plugin(Iq, ControlSet)
register_stanza_plugin(Message, ControlSet)

register_stanza_plugin(ControlSet, RequestNode, iterable=True)

register_stanza_plugin(ControlSet, BooleanParameter, iterable=True)
register_stanza_plugin(ControlSet, ColorParameter, iterable=True)
register_stanza_plugin(ControlSet, StringParameter, iterable=True)
register_stanza_plugin(ControlSet, DateParameter, iterable=True)
register_stanza_plugin(ControlSet, DateTimeParameter, iterable=True)
register_stanza_plugin(ControlSet, DoubleParameter, iterable=True)
register_stanza_plugin(ControlSet, DurationParameter, iterable=True)
register_stanza_plugin(ControlSet, IntParameter, iterable=True)
register_stanza_plugin(ControlSet, LongParameter, iterable=True)
register_stanza_plugin(ControlSet, TimeParameter, iterable=True)

register_stanza_plugin(Iq, ControlSetResponse)
register_stanza_plugin(ControlSetResponse, Error)
register_stanza_plugin(ControlSetResponse, RequestNode, iterable=True)
register_stanza_plugin(ControlSetResponse, ResponseParameter, iterable=True)

