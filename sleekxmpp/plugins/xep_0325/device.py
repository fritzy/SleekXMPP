"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Sustainable Innovation, Joachim.lindborg@sust.se, bjorn.westrom@consoden.se
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import datetime

class Device(object):
    """
    Example implementation of a device control object.

    The device object may by any custom implementation to support
    specific devices, but it must implement the functions:
          has_control_field
          set_control_fields
    """

    def __init__(self, nodeId):
        self.nodeId = nodeId
        self.control_fields = {}

    def has_control_field(self, field, typename):
        """
        Returns true if the supplied field name exists
        and the type matches for control in this device.

        Arguments:
            field      -- The field name
            typename   -- The expected type
        """
        if field in self.control_fields and self.control_fields[field]["type"] == typename:
            return True
        return False

    def set_control_fields(self, fields, session, callback):
        """
        Starts a control setting procedure. Verifies the fields,
        sets the data and (if needed) and calls the callback.

        Arguments:
            fields   -- List of control fields in tuple format:
                        (name, typename, value)
            session  -- Session id, only used in the callback as identifier
            callback -- Callback function to call when control set is complete.

                    The callback function must support the following arguments:

                session     -- Session id, as supplied in the
                               request_fields call
                nodeId      -- Identifier for this device
                result      -- The current result status of the readout.
                               Valid values are:
                               "error"  - Set fields failed.
                               "ok"     - All fields were set.
                error_field -- [optional] Only applies when result == "error"
                               The field name that failed
                               (usually means it is missing)
                error_msg   -- [optional] Only applies when result == "error".
                               Error details when a request failed.
        """

        if len(fields) > 0:
            # Check availiability
            for name, typename, value in fields:
                if not self.has_control_field(name, typename):
                    self._send_control_reject(session, name, "NotFound", callback)
                    return False

        for name, typename, value in fields:
            self._set_field_value(name, value)

        callback(session, result="ok", nodeId=self.nodeId)
        return True

    def _send_control_reject(self, session, field, message, callback):
        """
        Sends a reject to the caller

        Arguments:
            session  -- Session id, see definition in
                        set_control_fields function
            callback -- Callback function, see definition in
                        set_control_fields function
        """
        callback(session, result="error", nodeId=self.nodeId, error_field=field, error_msg=message)

    def _add_control_field(self, name, typename, value):
        """
        Adds a control field to the device

        Arguments:
            name     -- Name of the field
            typename -- Type of the field, one of:
                        (boolean, color, string, date, dateTime,
                         double, duration, int, long, time)
            value    -- Field value
        """
        self.control_fields[name] = {"type": typename, "value": value}

    def _set_field_value(self, name, value):
        """
        Set the value of a control field

        Arguments:
            name     -- Name of the field
            value    -- New value for the field
        """
        if name in self.control_fields:
            self.control_fields[name]["value"] = value

    def _get_field_value(self, name):
        """
        Get the value of a control field. Only used for unit testing.

        Arguments:
            name     -- Name of the field
        """
        if name in self.control_fields:
            return self.control_fields[name]["value"]
        return None
