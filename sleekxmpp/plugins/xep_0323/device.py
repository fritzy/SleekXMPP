"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Sustainable Innovation, Joachim.lindborg@sust.se, bjorn.westrom@consoden.se
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import datetime
import logging

class Device(object):
    """
    Example implementation of a device readout object.
    Is registered in the XEP_0323.register_node call
    The device object may be any custom implementation to support
    specific devices, but it must implement the functions:
          has_field
          request_fields
    """

    def __init__(self, nodeId, fields=None):
        if not fields:
            fields = {}

        self.nodeId = nodeId
        self.fields = fields # see fields described below
        # {'type':'numeric',
        #  'name':'myname',
        #  'value': 42,
        #  'unit':'Z'}];
        self.timestamp_data = {}
        self.momentary_data = {}
        self.momentary_timestamp = ""
        logging.debug("Device object started nodeId %s",nodeId)

    def has_field(self, field):
        """
        Returns true if the supplied field name exists in this device.

        Arguments:
            field      -- The field name
        """
        if field in self.fields.keys():
            return True
        return False

    def refresh(self, fields):
        """
        override method to do the refresh work
        refresh values from hardware or other
        """
        pass


    def request_fields(self, fields, flags, session, callback):
        """
        Starts a data readout. Verifies the requested fields,
        refreshes the data (if needed) and calls the callback
        with requested data.


        Arguments:
            fields   -- List of field names to readout
            flags    -- [optional] data classifier flags for the field, e.g. momentary
                        Formatted as a dictionary like { "flag name": "flag value" ... }
            session  -- Session id, only used in the callback as identifier
            callback -- Callback function to call when data is available.

                    The callback function must support the following arguments:

                session  -- Session id, as supplied in the request_fields call
                nodeId   -- Identifier for this device
                result   -- The current result status of the readout. Valid values are:
                               "error"  - Readout failed.
                               "fields" - Contains readout data.
                               "done"   - Indicates that the readout is complete. May contain
                                          readout data.
                timestamp_block -- [optional] Only applies when result != "error"
                               The readout data. Structured as a dictionary:
                  {
                    timestamp:     timestamp for this datablock,
                    fields:        list of field dictionary (one per readout field).
                      readout field dictionary format:
                      {
                        type:      The field type (numeric, boolean, dateTime, timeSpan, string, enum)
                        name:      The field name
                        value:     The field value
                        unit:      The unit of the field. Only applies to type numeric.
                        dataType:  The datatype of the field. Only applies to type enum.
                        flags:     [optional] data classifier flags for the field, e.g. momentary
                               Formatted as a dictionary like { "flag name": "flag value" ... }
                      }
                  }
                error_msg -- [optional] Only applies when result == "error".
                                Error details when a request failed.

        """
        logging.debug("request_fields called looking for fields %s",fields)
        if len(fields) > 0:
            # Check availiability
            for f in fields:
                if f not in self.fields.keys():
                    self._send_reject(session, callback)
                    return False
        else:
            # Request all fields
            fields = self.fields.keys()


        # Refresh data from device
        # ...
        logging.debug("about to refresh device fields %s",fields)
        self.refresh(fields)

        if "momentary" in flags and flags['momentary'] == "true" or \
           "all" in flags and flags['all'] == "true":
            ts_block = {}
            timestamp = ""

            if len(self.momentary_timestamp) > 0:
                timestamp = self.momentary_timestamp
            else:
                timestamp = self._get_timestamp()

            field_block = []
            for f in self.momentary_data:
                if f in fields:
                    field_block.append({"name": f,
                                "type": self.fields[f]["type"],
                                "unit": self.fields[f]["unit"],
                                "dataType": self.fields[f]["dataType"],
                                "value": self.momentary_data[f]["value"],
                                "flags": self.momentary_data[f]["flags"]})
            ts_block["timestamp"] = timestamp
            ts_block["fields"] = field_block

            callback(session, result="done", nodeId=self.nodeId, timestamp_block=ts_block)
            return

        from_flag = self._datetime_flag_parser(flags, 'from')
        to_flag = self._datetime_flag_parser(flags, 'to')

        for ts in sorted(self.timestamp_data.keys()):
            tsdt = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
            if not from_flag is None:
                if tsdt < from_flag:
                    #print (str(tsdt) + " < " + str(from_flag))
                    continue
            if not to_flag is None:
                if tsdt > to_flag:
                    #print (str(tsdt) + " > " + str(to_flag))
                    continue

            ts_block = {}
            field_block = []

            for f in self.timestamp_data[ts]:
                if f in fields:
                    field_block.append({"name": f,
                                "type": self.fields[f]["type"],
                                "unit": self.fields[f]["unit"],
                                "dataType": self.fields[f]["dataType"],
                                "value": self.timestamp_data[ts][f]["value"],
                                "flags": self.timestamp_data[ts][f]["flags"]})

            ts_block["timestamp"] = ts
            ts_block["fields"] = field_block
            callback(session, result="fields", nodeId=self.nodeId, timestamp_block=ts_block)
        callback(session, result="done", nodeId=self.nodeId, timestamp_block=None)

    def _datetime_flag_parser(self, flags, flagname):
        if not flagname in flags:
            return None

        dt = None
        try:
            dt = datetime.datetime.strptime(flags[flagname], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            # Badly formatted datetime, ignore it
            pass
        return dt


    def _get_timestamp(self):
        """
        Generates a properly formatted timestamp of current time
        """
        return datetime.datetime.now().replace(microsecond=0).isoformat()

    def _send_reject(self, session, callback):
        """
        Sends a reject to the caller

        Arguments:
            session  -- Session id, see definition in request_fields function
            callback -- Callback function, see definition in request_fields function
        """
        callback(session, result="error", nodeId=self.nodeId, timestamp_block=None, error_msg="Reject")

    def _add_field(self, name, typename, unit=None, dataType=None):
        """
        Adds a field to the device

        Arguments:
            name     -- Name of the field
            typename -- Type of the field (numeric, boolean, dateTime, timeSpan, string, enum)
            unit     -- [optional] only applies to "numeric". Unit for the field.
            dataType -- [optional] only applies to "enum". Datatype for the field.
        """
        self.fields[name] = {"type": typename, "unit": unit, "dataType": dataType}

    def _add_field_timestamp_data(self, name, timestamp, value, flags=None):
        """
        Adds timestamped data to a field

        Arguments:
            name      -- Name of the field
            timestamp -- Timestamp for the data (string)
            value     -- Field value at the timestamp
            flags     -- [optional] data classifier flags for the field, e.g. momentary
                         Formatted as a dictionary like { "flag name": "flag value" ... }
        """
        if not name in self.fields.keys():
            return False
        if not timestamp in self.timestamp_data:
            self.timestamp_data[timestamp] = {}

        self.timestamp_data[timestamp][name] = {"value": value, "flags": flags}
        return True

    def _add_field_momentary_data(self, name, value, flags=None):
        """
        Sets momentary data to a field

        Arguments:
            name      -- Name of the field
            value     -- Field value at the timestamp
            flags     -- [optional] data classifier flags for the field, e.g. momentary
                         Formatted as a dictionary like { "flag name": "flag value" ... }
        """
        if name not in self.fields:
            return False
        if flags is None:
            flags = {}

        flags["momentary"] = "true"
        self.momentary_data[name] = {"value": value, "flags": flags}
        return True

    def _set_momentary_timestamp(self, timestamp):
        """
        This function is only for unit testing to produce predictable results.
        """
        self.momentary_timestamp = timestamp

