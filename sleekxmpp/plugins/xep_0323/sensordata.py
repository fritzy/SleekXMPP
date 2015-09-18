"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Sustainable Innovation, Joachim.lindborg@sust.se, bjorn.westrom@consoden.se
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging
import time
import datetime
from threading import Thread, Lock, Timer

from sleekxmpp.plugins.xep_0323.timerreset import TimerReset

from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.plugins.base import BasePlugin
from sleekxmpp.plugins.xep_0323 import stanza
from sleekxmpp.plugins.xep_0323.stanza import Sensordata


log = logging.getLogger(__name__)


class XEP_0323(BasePlugin):

    """
    XEP-0323: IoT Sensor Data


    This XEP provides the underlying architecture, basic operations and data
    structures for sensor data communication over XMPP networks. It includes
    a hardware abstraction model, removing any technical detail implemented
    in underlying technologies.

    Also see <http://xmpp.org/extensions/xep-0323.html>

    Configuration Values:
        threaded -- Indicates if communication with sensors should be threaded.
                    Defaults to True.

    Events:
        Sensor side
        -----------
        Sensordata Event:Req    -- Received a request for data
        Sensordata Event:Cancel -- Received a cancellation for a request

        Client side
        -----------
        Sensordata Event:Accepted -- Received a accept from sensor for a request
        Sensordata Event:Rejected -- Received a reject from sensor for a request
        Sensordata Event:Cancelled -- Received a cancel confirm from sensor
        Sensordata Event:Fields   -- Received fields from sensor for a request
                                     This may be triggered multiple times since
                                     the sensor can split up its response in
                                     multiple messages.
        Sensordata Event:Failure  -- Received a failure indication from sensor
                                     for a request. Typically a comm timeout.

    Attributes:
        threaded -- Indicates if command events should be threaded.
                    Defaults to True.
        sessions -- A dictionary or equivalent backend mapping
                    session IDs to dictionaries containing data
                    relevant to a request's session. This dictionary is used
                    both by the client and sensor side. On client side, seqnr
                    is used as key, while on sensor side, a session_id is used
                    as key. This ensures that the two will not collide, so
                    one instance can be both client and sensor.
        Sensor side
        -----------
        nodes    -- A dictionary mapping sensor nodes that are serviced through
                    this XMPP instance to their device handlers ("drivers").
        Client side
        -----------
        last_seqnr -- The last used sequence number (integer). One sequence of
                    communication (e.g. -->request, <--accept, <--fields)
                    between client and sensor is identified by a unique
                    sequence number (unique between the client/sensor pair)

    Methods:
        plugin_init       -- Overrides base_plugin.plugin_init
        post_init         -- Overrides base_plugin.post_init
        plugin_end        -- Overrides base_plugin.plugin_end

        Sensor side
        -----------
        register_node     -- Register a sensor as available from this XMPP
                             instance.

        Client side
        -----------
        request_data      -- Initiates a request for data from one or more
                             sensors. Non-blocking, a callback function will
                             be called when data is available.

    """

    name = 'xep_0323'
    description = 'XEP-0323 Internet of Things - Sensor Data'
    dependencies = set(['xep_0030'])
    stanza = stanza


    default_config = {
        'threaded': True
    }

    def plugin_init(self):
        """ Start the XEP-0323 plugin """

        self.xmpp.register_handler(
                Callback('Sensordata Event:Req',
                    StanzaPath('iq@type=get/req'),
                    self._handle_event_req))

        self.xmpp.register_handler(
                Callback('Sensordata Event:Accepted',
                    StanzaPath('iq@type=result/accepted'),
                    self._handle_event_accepted))

        self.xmpp.register_handler(
                Callback('Sensordata Event:Rejected',
                    StanzaPath('iq@type=error/rejected'),
                    self._handle_event_rejected))

        self.xmpp.register_handler(
                Callback('Sensordata Event:Cancel',
                    StanzaPath('iq@type=get/cancel'),
                    self._handle_event_cancel))

        self.xmpp.register_handler(
                Callback('Sensordata Event:Cancelled',
                    StanzaPath('iq@type=result/cancelled'),
                    self._handle_event_cancelled))

        self.xmpp.register_handler(
                Callback('Sensordata Event:Fields',
                    StanzaPath('message/fields'),
                    self._handle_event_fields))

        self.xmpp.register_handler(
                Callback('Sensordata Event:Failure',
                    StanzaPath('message/failure'),
                    self._handle_event_failure))

        self.xmpp.register_handler(
                Callback('Sensordata Event:Started',
                    StanzaPath('message/started'),
                    self._handle_event_started))

        # Server side dicts
        self.nodes = {}
        self.sessions = {}

        self.last_seqnr = 0
        self.seqnr_lock = Lock()

        ## For testing only
        self.test_authenticated_from = ""

    def post_init(self):
        """ Init complete. Register our features in Service discovery. """
        BasePlugin.post_init(self)
        self.xmpp['xep_0030'].add_feature(Sensordata.namespace)
        self.xmpp['xep_0030'].set_items(node=Sensordata.namespace, items=tuple())

    def _new_session(self):
        """ Return a new session ID. """
        return str(time.time()) + '-' + self.xmpp.new_id()

    def session_bind(self, jid):
        logging.debug("setting the Disco discovery for %s" % Sensordata.namespace)
        self.xmpp['xep_0030'].add_feature(Sensordata.namespace)
        self.xmpp['xep_0030'].set_items(node=Sensordata.namespace, items=tuple())


    def plugin_end(self):
        """ Stop the XEP-0323 plugin """
        self.sessions.clear()
        self.xmpp.remove_handler('Sensordata Event:Req')
        self.xmpp.remove_handler('Sensordata Event:Accepted')
        self.xmpp.remove_handler('Sensordata Event:Rejected')
        self.xmpp.remove_handler('Sensordata Event:Cancel')
        self.xmpp.remove_handler('Sensordata Event:Cancelled')
        self.xmpp.remove_handler('Sensordata Event:Fields')
        self.xmpp['xep_0030'].del_feature(feature=Sensordata.namespace)


    # =================================================================
    # Sensor side (data provider) API

    def register_node(self, nodeId, device, commTimeout, sourceId=None, cacheType=None):
        """
        Register a sensor/device as available for serving of data through this XMPP
        instance.

        The device object may by any custom implementation to support
        specific devices, but it must implement the functions:
          has_field
          request_fields
        according to the interfaces shown in the example device.py file.

        Arguments:
            nodeId      -- The identifier for the device
            device      -- The device object
            commTimeout -- Time in seconds to wait between each callback from device during
                           a data readout. Float.
            sourceId    -- [optional] identifying the data source controlling the device
            cacheType   -- [optional] narrowing down the search to a specific kind of node
        """
        self.nodes[nodeId] = {"device": device,
                                "commTimeout": commTimeout,
                                "sourceId": sourceId,
                                "cacheType": cacheType}

    def _set_authenticated(self, auth=''):
        """ Internal testing function """
        self.test_authenticated_from = auth


    def _handle_event_req(self, iq):
        """
        Event handler for reception of an Iq with req - this is a request.

        Verifies that
          - all the requested nodes are available
          - at least one of the requested fields is available from at least
            one of the nodes

        If the request passes verification, an accept response is sent, and
        the readout process is started in a separate thread.
        If the verification fails, a reject message is sent.
        """

        seqnr = iq['req']['seqnr']
        error_msg = ''
        req_ok = True

        # Authentication
        if len(self.test_authenticated_from) > 0 and not iq['from'] == self.test_authenticated_from:
            # Invalid authentication
            req_ok = False
            error_msg = "Access denied"

        # Nodes
        process_nodes = []
        if len(iq['req']['nodes']) > 0:
            for n in iq['req']['nodes']:
                if not n['nodeId'] in self.nodes:
                    req_ok = False
                    error_msg = "Invalid nodeId " + n['nodeId']
            process_nodes = [n['nodeId'] for n in iq['req']['nodes']]
        else:
            process_nodes = self.nodes.keys()

        # Fields - if we just find one we are happy, otherwise we reject
        process_fields = []
        if len(iq['req']['fields']) > 0:
            found = False
            for f in iq['req']['fields']:
                for node in self.nodes:
                    if self.nodes[node]["device"].has_field(f['name']):
                        found = True
                        break
            if not found:
                req_ok = False
                error_msg = "Invalid field " + f['name']
            process_fields = [f['name'] for n in iq['req']['fields']]

        req_flags = iq['req']._get_flags()

        request_delay_sec = None
        if 'when' in req_flags:
            # Timed request - requires datetime string in iso format
            # ex. 2013-04-05T15:00:03
            dt = None
            try:
                dt = datetime.datetime.strptime(req_flags['when'], "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                req_ok = False
                error_msg = "Invalid datetime in 'when' flag, please use ISO format (i.e. 2013-04-05T15:00:03)."

            if not dt is None:
                # Datetime properly formatted
                dtnow = datetime.datetime.now()
                dtdiff = dt - dtnow
                request_delay_sec = dtdiff.seconds + dtdiff.days * 24 * 3600
                if request_delay_sec <= 0:
                    req_ok = False
                    error_msg = "Invalid datetime in 'when' flag, cannot set a time in the past. Current time: " + dtnow.isoformat()

        if req_ok:
            session = self._new_session()
            self.sessions[session] = {"from": iq['from'], "to": iq['to'], "seqnr": seqnr}
            self.sessions[session]["commTimers"] = {}
            self.sessions[session]["nodeDone"] = {}

            iq.reply()
            iq['accepted']['seqnr'] = seqnr
            if not request_delay_sec is None:
                iq['accepted']['queued'] = "true"
            iq.send(block=False)

            self.sessions[session]["node_list"] = process_nodes

            if not request_delay_sec is None:
                # Delay request to requested time
                timer = Timer(request_delay_sec, self._event_delayed_req, args=(session, process_fields, req_flags))
                self.sessions[session]["commTimers"]["delaytimer"] = timer
                timer.start()
                return

            if self.threaded:
                tr_req = Thread(target=self._threaded_node_request, args=(session, process_fields, req_flags))
                tr_req.start()
            else:
                self._threaded_node_request(session, process_fields, req_flags)

        else:
            iq.reply()
            iq['type'] = 'error'
            iq['rejected']['seqnr'] = seqnr
            iq['rejected']['error'] = error_msg
            iq.send(block=False)

    def _threaded_node_request(self, session, process_fields, flags):
        """
        Helper function to handle the device readouts in a separate thread.

        Arguments:
            session         -- The request session id
            process_fields  -- The fields to request from the devices
            flags           -- [optional] flags to pass to the devices, e.g. momentary
                               Formatted as a dictionary like { "flag name": "flag value" ... }
        """
        for node in self.sessions[session]["node_list"]:
            self.sessions[session]["nodeDone"][node] = False

        for node in self.sessions[session]["node_list"]:
            timer = TimerReset(self.nodes[node]['commTimeout'], self._event_comm_timeout, args=(session, node))
            self.sessions[session]["commTimers"][node] = timer
            timer.start()
            self.nodes[node]['device'].request_fields(process_fields, flags=flags, session=session, callback=self._device_field_request_callback)

    def _event_comm_timeout(self, session, nodeId):
        """
        Triggered if any of the readout operations timeout.
        Sends a failure message back to the client, stops communicating
        with the failing device.

        Arguments:
            session         -- The request session id
            nodeId          -- The id of the device which timed out
        """
        msg = self.xmpp.Message()
        msg['from'] = self.sessions[session]['to']
        msg['to'] = self.sessions[session]['from']
        msg['failure']['seqnr'] = self.sessions[session]['seqnr']
        msg['failure']['error']['text'] = "Timeout"
        msg['failure']['error']['nodeId'] = nodeId
        msg['failure']['error']['timestamp'] = datetime.datetime.now().replace(microsecond=0).isoformat()

        # Drop communication with this device and check if we are done
        self.sessions[session]["nodeDone"][nodeId] = True
        if (self._all_nodes_done(session)):
            msg['failure']['done'] = 'true'
        msg.send()
        # The session is complete, delete it
        del self.sessions[session]

    def _event_delayed_req(self, session, process_fields, req_flags):
        """
        Triggered when the timer from a delayed request fires.

        Arguments:
            session         -- The request session id
            process_fields  -- The fields to request from the devices
            flags           -- [optional] flags to pass to the devices, e.g. momentary
                               Formatted as a dictionary like { "flag name": "flag value" ... }
        """
        msg = self.xmpp.Message()
        msg['from'] = self.sessions[session]['to']
        msg['to'] = self.sessions[session]['from']
        msg['started']['seqnr'] = self.sessions[session]['seqnr']
        msg.send()

        if self.threaded:
            tr_req = Thread(target=self._threaded_node_request, args=(session, process_fields, req_flags))
            tr_req.start()
        else:
            self._threaded_node_request(session, process_fields, req_flags)

    def _all_nodes_done(self, session):
        """
        Checks whether all devices are done replying to the readout.

        Arguments:
            session         -- The request session id
        """
        for n in self.sessions[session]["nodeDone"]:
            if not self.sessions[session]["nodeDone"][n]:
                return False
        return True

    def _device_field_request_callback(self, session, nodeId, result, timestamp_block, error_msg=None):
        """
        Callback function called by the devices when they have any additional data.
        Composes a message with the data and sends it back to the client, and resets
        the timeout timer for the device.

        Arguments:
            session         -- The request session id
            nodeId          -- The device id which initiated the callback
            result          -- The current result status of the readout. Valid values are:
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
            error_msg        -- [optional] Only applies when result == "error".
                                Error details when a request failed.
        """
        if not session in self.sessions:
            # This can happen if a session was deleted, like in a cancellation. Just drop the data.
            return

        if result == "error":
            self.sessions[session]["commTimers"][nodeId].cancel()

            msg = self.xmpp.Message()
            msg['from'] = self.sessions[session]['to']
            msg['to'] = self.sessions[session]['from']
            msg['failure']['seqnr'] = self.sessions[session]['seqnr']
            msg['failure']['error']['text'] = error_msg
            msg['failure']['error']['nodeId'] = nodeId
            msg['failure']['error']['timestamp'] = datetime.datetime.now().replace(microsecond=0).isoformat()

            # Drop communication with this device and check if we are done
            self.sessions[session]["nodeDone"][nodeId] = True
            if (self._all_nodes_done(session)):
                msg['failure']['done'] = 'true'
                # The session is complete, delete it
                del self.sessions[session]
            msg.send()
        else:
            msg = self.xmpp.Message()
            msg['from'] = self.sessions[session]['to']
            msg['to'] = self.sessions[session]['from']
            msg['fields']['seqnr'] = self.sessions[session]['seqnr']

            if timestamp_block is not None and len(timestamp_block) > 0:
                node = msg['fields'].add_node(nodeId)
                ts = node.add_timestamp(timestamp_block["timestamp"])

                for f in timestamp_block["fields"]:
                    data = ts.add_data( typename=f['type'],
                                        name=f['name'],
                                        value=f['value'],
                                        unit=f['unit'],
                                        dataType=f['dataType'],
                                        flags=f['flags'])

            if result == "done":
                self.sessions[session]["commTimers"][nodeId].cancel()
                self.sessions[session]["nodeDone"][nodeId] = True
                if (self._all_nodes_done(session)):
                    # The session is complete, delete it
                    del self.sessions[session]
                    msg['fields']['done'] = 'true'
            else:
                # Restart comm timer
                self.sessions[session]["commTimers"][nodeId].reset()

            msg.send()

    def _handle_event_cancel(self, iq):
        """ Received Iq with cancel - this is a cancel request.
        Delete the session and confirm. """

        seqnr = iq['cancel']['seqnr']
        # Find the session
        for s in self.sessions:
            if self.sessions[s]['from'] == iq['from'] and self.sessions[s]['to'] == iq['to'] and self.sessions[s]['seqnr'] == seqnr:
                # found it. Cancel all timers
                for n in self.sessions[s]["commTimers"]:
                    self.sessions[s]["commTimers"][n].cancel()

                # Confirm
                iq.reply()
                iq['type'] = 'result'
                iq['cancelled']['seqnr'] = seqnr
                iq.send(block=False)

                # Delete session
                del self.sessions[s]
                return

        # Could not find session, send reject
        iq.reply()
        iq['type'] = 'error'
        iq['rejected']['seqnr'] = seqnr
        iq['rejected']['error'] = "Cancel request received, no matching request is active."
        iq.send(block=False)

        # =================================================================
    # Client side (data retriever) API

    def request_data(self, from_jid, to_jid, callback, nodeIds=None, fields=None, flags=None):
        """
        Called on the client side to initiate a data readout.
        Composes a message with the request and sends it to the device(s).
        Does not block, the callback will be called when data is available.

        Arguments:
            from_jid        -- The jid of the requester
            to_jid          -- The jid of the device(s)
            callback        -- The callback function to call when data is available.

                            The callback function must support the following arguments:

                from_jid    -- The jid of the responding device(s)
                result      -- The current result status of the readout. Valid values are:
                               "accepted"  - Readout request accepted
                               "queued"    - Readout request accepted and queued
                               "rejected"  - Readout request rejected
                               "failure"   - Readout failed.
                               "cancelled" - Confirmation of request cancellation.
                               "started"   - Previously queued request is now started
                               "fields"    - Contains readout data.
                               "done"      - Indicates that the readout is complete.

                nodeId      -- [optional] Mandatory when result == "fields" or "failure".
                               The node Id of the responding device. One callback will only
                               contain data from one device.
                timestamp   -- [optional] Mandatory when result == "fields".
                               The timestamp of data in this callback. One callback will only
                               contain data from one timestamp.
                fields      -- [optional] Mandatory when result == "fields".
                               List of field dictionaries representing the readout data.
                               Dictionary format:
                  {
                    typename:  The field type (numeric, boolean, dateTime, timeSpan, string, enum)
                    name:      The field name
                    value:     The field value
                    unit:      The unit of the field. Only applies to type numeric.
                    dataType:  The datatype of the field. Only applies to type enum.
                    flags:     [optional] data classifier flags for the field, e.g. momentary.
                               Formatted as a dictionary like { "flag name": "flag value" ... }
                  }

                error_msg   -- [optional] Mandatory when result == "rejected" or "failure".
                               Details about why the request is rejected or failed.
                               "rejected" means that the request is stopped, but note that the
                               request will continue even after a "failure". "failure" only means
                               that communication was stopped to that specific device, other
                               device(s) (if any) will continue their readout.

            nodeIds      -- [optional] Limits the request to the node Ids in this list.
            fields       -- [optional] Limits the request to the field names in this list.
            flags        -- [optional] Limits the request according to the flags, or sets
                            readout conditions such as timing.

        Return value:
            session      -- Session identifier. Client can use this as a reference to cancel
                            the request.
        """
        iq = self.xmpp.Iq()
        iq['from'] = from_jid
        iq['to'] = to_jid
        iq['type'] = "get"
        seqnr = self._get_new_seqnr()
        iq['id'] = seqnr
        iq['req']['seqnr'] = seqnr
        if nodeIds is not None:
            for nodeId in nodeIds:
                iq['req'].add_node(nodeId)
        if fields is not None:
            for field in fields:
                iq['req'].add_field(field)

        iq['req']._set_flags(flags)

        self.sessions[seqnr] = {"from": iq['from'], "to": iq['to'], "seqnr": seqnr, "callback": callback}
        iq.send(block=False)

        return seqnr

    def cancel_request(self, session):
        """
        Called on the client side to cancel a request for data readout.
        Composes a message with the cancellation and sends it to the device(s).
        Does not block, the callback will be called when cancellation is
        confirmed.

        Arguments:
            session        -- The session id of the request to cancel
        """
        seqnr = session
        iq = self.xmpp.Iq()
        iq['from'] = self.sessions[seqnr]['from']
        iq['to'] = self.sessions[seqnr]['to']
        iq['type'] = "get"
        iq['id'] = seqnr
        iq['cancel']['seqnr'] = seqnr
        iq.send(block=False)

    def _get_new_seqnr(self):
        """ Returns a unique sequence number (unique across threads) """
        self.seqnr_lock.acquire()
        self.last_seqnr += 1
        self.seqnr_lock.release()
        return str(self.last_seqnr)

    def _handle_event_accepted(self, iq):
        """ Received Iq with accepted - request was accepted """
        seqnr = iq['accepted']['seqnr']
        result = "accepted"
        if iq['accepted']['queued'] == 'true':
            result = "queued"

        callback = self.sessions[seqnr]["callback"]
        callback(from_jid=iq['from'], result=result)

    def _handle_event_rejected(self, iq):
        """ Received Iq with rejected - this is a reject.
        Delete the session. """
        seqnr = iq['rejected']['seqnr']
        callback = self.sessions[seqnr]["callback"]
        callback(from_jid=iq['from'], result="rejected", error_msg=iq['rejected']['error'])
        # Session terminated
        del self.sessions[seqnr]

    def _handle_event_cancelled(self, iq):
        """
        Received Iq with cancelled - this is a cancel confirm.
        Delete the session.
        """
        seqnr = iq['cancelled']['seqnr']
        callback = self.sessions[seqnr]["callback"]
        callback(from_jid=iq['from'], result="cancelled")
        # Session cancelled
        del self.sessions[seqnr]

    def _handle_event_fields(self, msg):
        """
        Received Msg with fields - this is a data response to a request.
        If this is the last data block, issue a "done" callback.
        """
        seqnr = msg['fields']['seqnr']
        callback = self.sessions[seqnr]["callback"]
        for node in msg['fields']['nodes']:
            for ts in node['timestamps']:
                fields = []
                for d in ts['datas']:
                    field_block = {}
                    field_block["name"] = d['name']
                    field_block["typename"] = d._get_typename()
                    field_block["value"] = d['value']
                    if not d['unit'] == "": field_block["unit"] = d['unit'];
                    if not d['dataType'] == "": field_block["dataType"] = d['dataType'];
                    flags = d._get_flags()
                    if not len(flags) == 0:
                        field_block["flags"] = flags
                    fields.append(field_block)

                callback(from_jid=msg['from'], result="fields", nodeId=node['nodeId'], timestamp=ts['value'], fields=fields)

        if msg['fields']['done'] == "true":
            callback(from_jid=msg['from'], result="done")
            # Session done
            del self.sessions[seqnr]

    def _handle_event_failure(self, msg):
        """
        Received Msg with failure - our request failed
        Delete the session.
        """
        seqnr = msg['failure']['seqnr']
        callback = self.sessions[seqnr]["callback"]
        callback(from_jid=msg['from'], result="failure", nodeId=msg['failure']['error']['nodeId'], timestamp=msg['failure']['error']['timestamp'], error_msg=msg['failure']['error']['text'])

        # Session failed
        del self.sessions[seqnr]

    def _handle_event_started(self, msg):
        """
        Received Msg with started - our request was queued and is now started.
        """
        seqnr = msg['started']['seqnr']
        callback = self.sessions[seqnr]["callback"]
        callback(from_jid=msg['from'], result="started")


