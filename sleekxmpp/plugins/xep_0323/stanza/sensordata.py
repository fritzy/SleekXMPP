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

class Sensordata(ElementBase):
    """ Placeholder for the namespace, not used as a stanza """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'sensordata'
    plugin_attrib = name
    interfaces = set(tuple())

class FieldTypes():
    """
    All field types are optional booleans that default to False
    """
    field_types = set([ 'momentary','peak','status','computed','identity','historicalSecond','historicalMinute','historicalHour', \
                        'historicalDay','historicalWeek','historicalMonth','historicalQuarter','historicalYear','historicalOther'])

class FieldStatus():
    """
    All field statuses are optional booleans that default to False
    """
    field_status = set([ 'missing','automaticEstimate','manualEstimate','manualReadout','automaticReadout','timeOffset','warning','error', \
                         'signed','invoiced','endOfSeries','powerFailure','invoiceConfirmed'])

class Request(ElementBase):
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'req'
    plugin_attrib = name
    interfaces = set(['seqnr','nodes','fields','serviceToken','deviceToken','userToken','from','to','when','historical','all'])
    interfaces.update(FieldTypes.field_types)
    _flags = set(['serviceToken','deviceToken','userToken','from','to','when','historical','all'])
    _flags.update(FieldTypes.field_types)

    def __init__(self, xml=None, parent=None):
        ElementBase.__init__(self, xml, parent)
        self._nodes = set()
        self._fields = set()

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
        self._fields = set([field['name'] for field in self['fields']])

    def _get_flags(self):
        """
        Helper function for getting of flags. Returns all flags in
        dictionary format: { "flag name": "flag value" ... }
        """
        flags = {}
        for f in self._flags:
            if not self[f] == "":
                flags[f] = self[f]
        return flags

    def _set_flags(self, flags):
        """
        Helper function for setting of flags.

        Arguments:
            flags -- Flags in dictionary format: { "flag name": "flag value" ... }
        """
        for f in self._flags:
            if flags is not None and f in flags:
                self[f] = flags[f]
            else:
                self[f] = None

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


    def add_field(self, name):
        """
        Add a new field element. Each item is required to have a
        name.

        Arguments:
            name  -- The name of the field.
        """
        if name not in self._fields:
            self._fields.add((name))
            field = RequestField(parent=self)
            field['name'] = name
            self.iterables.append(field)
            return field
        return None

    def del_field(self, name):
        """
        Remove a single field.

        Arguments:
            name  -- name of field to remove.
        """
        if name in self._fields:
            fields = [i for i in self.iterables if isinstance(i, RequestField)]
            for field in fields:
                if field['name'] == name:
                    self.xml.remove(field.xml)
                    self.iterables.remove(field)
                    return True
        return False

    def get_fields(self):
        """Return all fields."""
        fields = []
        for field in self['substanzas']:
            if isinstance(field, RequestField):
                fields.append(field)
        return fields

    def set_fields(self, fields):
        """
        Set or replace all fields. The given fields must be in a
        list or set where each item is RequestField or string

        Arguments:
            fields -- A series of fields in RequestField or string format.
        """
        self.del_fields()
        for field in fields:
            if isinstance(field, RequestField):
                self.add_field(field['name'])
            else:
                self.add_field(field)

    def del_fields(self):
        """Remove all fields."""
        self._fields = set()
        fields = [i for i in self.iterables if isinstance(i, RequestField)]
        for field in fields:
            self.xml.remove(field.xml)
            self.iterables.remove(field)


class RequestNode(ElementBase):
    """ Node element in a request """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'node'
    plugin_attrib = name
    interfaces = set(['nodeId','sourceId','cacheType'])

class RequestField(ElementBase):
    """ Field element in a request """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'field'
    plugin_attrib = name
    interfaces = set(['name'])

class Accepted(ElementBase):
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'accepted'
    plugin_attrib = name
    interfaces = set(['seqnr','queued'])

class Started(ElementBase):
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'started'
    plugin_attrib = name
    interfaces = set(['seqnr'])

class Failure(ElementBase):
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'failure'
    plugin_attrib = name
    interfaces = set(['seqnr','done'])

class Error(ElementBase):
    """ Error element in a request failure """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'error'
    plugin_attrib = name
    interfaces = set(['nodeId','timestamp','sourceId','cacheType','text'])

    def get_text(self):
        """Return then contents inside the XML tag."""
        return self.xml.text

    def set_text(self, value):
        """Set then contents inside the XML tag.

        :param value: string
        """

        self.xml.text = value
        return self

    def del_text(self):
        """Remove the contents inside the XML tag."""
        self.xml.text = ""
        return self

class Rejected(ElementBase):
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'rejected'
    plugin_attrib = name
    interfaces = set(['seqnr','error'])
    sub_interfaces = set(['error'])

class Fields(ElementBase):
    """ Fields element, top level in a response message with data """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'fields'
    plugin_attrib = name
    interfaces = set(['seqnr','done','nodes'])

    def __init__(self, xml=None, parent=None):
        ElementBase.__init__(self, xml, parent)
        self._nodes = set()

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


    def add_node(self, nodeId, sourceId=None, cacheType=None, substanzas=None):
        """
        Add a new node element. Each item is required to have a
        nodeId, but may also specify a sourceId value and cacheType.

        Arguments:
            nodeId  -- The ID for the node.
            sourceId  -- [optional] identifying the data source controlling the device
            cacheType -- [optional] narrowing down the search to a specific kind of node
        """
        if nodeId not in self._nodes:
            self._nodes.add((nodeId))
            node = FieldsNode(parent=self)
            node['nodeId'] = nodeId
            node['sourceId'] = sourceId
            node['cacheType'] = cacheType
            if substanzas is not None:
                node.set_timestamps(substanzas)

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
            nodes = [i for i in self.iterables if isinstance(i, FieldsNode)]
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
            if isinstance(node, FieldsNode):
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
        #print(str(id(self)) + " set_nodes: got " + str(nodes))
        self.del_nodes()
        for node in nodes:
            if isinstance(node, FieldsNode):
                self.add_node(node['nodeId'], node['sourceId'], node['cacheType'], substanzas=node['substanzas'])
            else:
                nodeId, sourceId, cacheType = node
                self.add_node(nodeId, sourceId, cacheType)

    def del_nodes(self):
        """Remove all nodes."""
        self._nodes = set()
        nodes = [i for i in self.iterables if isinstance(i, FieldsNode)]
        for node in nodes:
            self.xml.remove(node.xml)
            self.iterables.remove(node)


class FieldsNode(ElementBase):
    """ Node element in response fields """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'node'
    plugin_attrib = name
    interfaces = set(['nodeId','sourceId','cacheType','timestamps'])

    def __init__(self, xml=None, parent=None):
        ElementBase.__init__(self, xml, parent)
        self._timestamps = set()

    def setup(self, xml=None):
        """
        Populate the stanza object using an optional XML object.

        Overrides ElementBase.setup

        Caches item information.

        Arguments:
            xml -- Use an existing XML object for the stanza's values.
        """
        ElementBase.setup(self, xml)
        self._timestamps = set([ts['value'] for ts in self['timestamps']])

    def add_timestamp(self, timestamp, substanzas=None):
        """
        Add a new timestamp element.

        Arguments:
            timestamp  -- The timestamp in ISO format.
        """
        #print(str(id(self)) + " add_timestamp: " + str(timestamp))

        if timestamp not in self._timestamps:
            self._timestamps.add((timestamp))
            ts = Timestamp(parent=self)
            ts['value'] = timestamp
            if not substanzas is None:
                ts.set_datas(substanzas)
                #print("add_timestamp with substanzas: " + str(substanzas))
            self.iterables.append(ts)
            #print(str(id(self)) + " added_timestamp: " + str(id(ts)))
            return ts
        return None

    def del_timestamp(self, timestamp):
        """
        Remove a single timestamp.

        Arguments:
            timestamp  -- timestamp (in ISO format) of the item to remove.
        """
        #print("del_timestamp: ")
        if timestamp in self._timestamps:
            timestamps = [i for i in self.iterables if isinstance(i, Timestamp)]
            for ts in timestamps:
                if ts['value'] == timestamp:
                    self.xml.remove(ts.xml)
                    self.iterables.remove(ts)
                    return True
        return False

    def get_timestamps(self):
        """Return all timestamps."""
        #print(str(id(self)) + " get_timestamps: ")
        timestamps = []
        for timestamp in self['substanzas']:
            if isinstance(timestamp, Timestamp):
                timestamps.append(timestamp)
        return timestamps

    def set_timestamps(self, timestamps):
        """
        Set or replace all timestamps. The given timestamps must be in a
        list or set where each item is a timestamp

        Arguments:
            timestamps -- A series of timestamps.
        """
        #print(str(id(self)) + " set_timestamps: got " + str(timestamps))
        self.del_timestamps()
        for timestamp in timestamps:
            #print("set_timestamps: subset " + str(timestamp))
            #print("set_timestamps: subset.substanzas " + str(timestamp['substanzas']))
            if isinstance(timestamp, Timestamp):
                self.add_timestamp(timestamp['value'], substanzas=timestamp['substanzas'])
            else:
                #print("set_timestamps: got " + str(timestamp))
                self.add_timestamp(timestamp)

    def del_timestamps(self):
        """Remove all timestamps."""
        #print(str(id(self)) + " del_timestamps: ")
        self._timestamps = set()
        timestamps = [i for i in self.iterables if isinstance(i, Timestamp)]
        for timestamp in timestamps:
            self.xml.remove(timestamp.xml)
            self.iterables.remove(timestamp)

class Field(ElementBase):
    """
    Field element in response Timestamp. This is a base class,
    all instances of fields added to Timestamp must be of types:
        DataNumeric
        DataString
        DataBoolean
        DataDateTime
        DataTimeSpan
        DataEnum
    """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'field'
    plugin_attrib = name
    interfaces = set(['name','module','stringIds'])
    interfaces.update(FieldTypes.field_types)
    interfaces.update(FieldStatus.field_status)

    _flags = set()
    _flags.update(FieldTypes.field_types)
    _flags.update(FieldStatus.field_status)

    def set_stringIds(self, value):
        """Verifies stringIds according to regexp from specification XMPP-0323.

        :param value: string
        """

        pattern = re.compile("^\d+([|]\w+([.]\w+)*([|][^,]*)?)?(,\d+([|]\w+([.]\w+)*([|][^,]*)?)?)*$")
        if pattern.match(value) is not None:
            self.xml.stringIds = value
        else:
            # Bad content, add nothing
            pass

        return self

    def _get_flags(self):
        """
        Helper function for getting of flags. Returns all flags in
        dictionary format: { "flag name": "flag value" ... }
        """
        flags = {}
        for f in self._flags:
            if not self[f] == "":
                flags[f] = self[f]
        return flags

    def _set_flags(self, flags):
        """
        Helper function for setting of flags.

        Arguments:
            flags -- Flags in dictionary format: { "flag name": "flag value" ... }
        """
        for f in self._flags:
            if flags is not None and f in flags:
                self[f] = flags[f]
            else:
                self[f] = None

    def _get_typename(self):
        return "invalid type, use subclasses!"


class Timestamp(ElementBase):
    """ Timestamp element in response Node """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'timestamp'
    plugin_attrib = name
    interfaces = set(['value','datas'])

    def __init__(self, xml=None, parent=None):
        ElementBase.__init__(self, xml, parent)
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
        self._datas = set([data['name'] for data in self['datas']])

    def add_data(self, typename, name, value, module=None, stringIds=None, unit=None, dataType=None, flags=None):
        """
        Add a new data element.

        Arguments:
            typename   -- The type of data element (numeric, string, boolean, dateTime, timeSpan or enum)
            value      -- The value of the data element
            module     -- [optional] language module to use for the data element
            stringIds  -- [optional] The stringIds used to find associated text in the language module
            unit       -- [optional] The unit. Only applicable for type numeric
            dataType   -- [optional] The dataType. Only applicable for type enum
        """
        if name not in self._datas:
            dataObj = None
            if typename == "numeric":
                dataObj = DataNumeric(parent=self)
                dataObj['unit'] = unit
            elif typename == "string":
                dataObj = DataString(parent=self)
            elif typename == "boolean":
                dataObj = DataBoolean(parent=self)
            elif typename == "dateTime":
                dataObj = DataDateTime(parent=self)
            elif typename == "timeSpan":
                dataObj = DataTimeSpan(parent=self)
            elif typename == "enum":
                dataObj = DataEnum(parent=self)
                dataObj['dataType'] = dataType

            dataObj['name'] = name
            dataObj['value'] = value
            dataObj['module'] = module
            dataObj['stringIds'] = stringIds

            if flags is not None:
                dataObj._set_flags(flags)

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
            datas = [i for i in self.iterables if isinstance(i, Field)]
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
            if isinstance(data, Field):
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
            self.add_data(typename=data._get_typename(), name=data['name'], value=data['value'], module=data['module'], stringIds=data['stringIds'], unit=data['unit'], dataType=data['dataType'], flags=data._get_flags())

    def del_datas(self):
        """Remove all data elements."""
        self._datas = set()
        datas = [i for i in self.iterables if isinstance(i, Field)]
        for data in datas:
            self.xml.remove(data.xml)
            self.iterables.remove(data)

class DataNumeric(Field):
    """
    Field data of type numeric.
    Note that the value is expressed as a string.
    """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'numeric'
    plugin_attrib = name
    interfaces = set(['value', 'unit'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return "numeric"

class DataString(Field):
    """
    Field data of type string
    """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'string'
    plugin_attrib = name
    interfaces = set(['value'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return "string"

class DataBoolean(Field):
    """
    Field data of type boolean.
    Note that the value is expressed as a string.
    """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'boolean'
    plugin_attrib = name
    interfaces = set(['value'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return "boolean"

class DataDateTime(Field):
    """
    Field data of type dateTime.
    Note that the value is expressed as a string.
    """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'dateTime'
    plugin_attrib = name
    interfaces = set(['value'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return "dateTime"

class DataTimeSpan(Field):
    """
    Field data of type timeSpan.
    Note that the value is expressed as a string.
    """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'timeSpan'
    plugin_attrib = name
    interfaces = set(['value'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return "timeSpan"

class DataEnum(Field):
    """
    Field data of type enum.
    Note that the value is expressed as a string.
    """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'enum'
    plugin_attrib = name
    interfaces = set(['value', 'dataType'])
    interfaces.update(Field.interfaces)

    def _get_typename(self):
        return "enum"

class Done(ElementBase):
    """ Done element used to signal that all data has been transferred """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'done'
    plugin_attrib = name
    interfaces = set(['seqnr'])

class Cancel(ElementBase):
    """ Cancel element used to signal that a request shall be cancelled """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'cancel'
    plugin_attrib = name
    interfaces = set(['seqnr'])

class Cancelled(ElementBase):
    """ Cancelled element used to signal that cancellation is confirmed """
    namespace = 'urn:xmpp:iot:sensordata'
    name = 'cancelled'
    plugin_attrib = name
    interfaces = set(['seqnr'])


register_stanza_plugin(Iq, Request)
register_stanza_plugin(Request, RequestNode, iterable=True)
register_stanza_plugin(Request, RequestField, iterable=True)

register_stanza_plugin(Iq, Accepted)
register_stanza_plugin(Message, Failure)
register_stanza_plugin(Failure, Error)

register_stanza_plugin(Iq, Rejected)

register_stanza_plugin(Message, Fields)
register_stanza_plugin(Fields, FieldsNode, iterable=True)
register_stanza_plugin(FieldsNode, Timestamp, iterable=True)
register_stanza_plugin(Timestamp, Field, iterable=True)
register_stanza_plugin(Timestamp, DataNumeric, iterable=True)
register_stanza_plugin(Timestamp, DataString, iterable=True)
register_stanza_plugin(Timestamp, DataBoolean, iterable=True)
register_stanza_plugin(Timestamp, DataDateTime, iterable=True)
register_stanza_plugin(Timestamp, DataTimeSpan, iterable=True)
register_stanza_plugin(Timestamp, DataEnum, iterable=True)

register_stanza_plugin(Message, Started)

register_stanza_plugin(Iq, Cancel)
register_stanza_plugin(Iq, Cancelled)
