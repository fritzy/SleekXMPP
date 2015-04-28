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
from threading import Thread, Timer, Lock

from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.plugins.base import BasePlugin
from sleekxmpp.plugins.xep_0325 import stanza
from sleekxmpp.plugins.xep_0325.stanza import Control


log = logging.getLogger(__name__)


class XEP_0325(BasePlugin):

    """
    XEP-0325: IoT Control


    Actuators are devices in sensor networks that can be controlled through
    the network and act with the outside world. In sensor networks and
    Internet of Things applications, actuators make it possible to automate
    real-world processes.
    This plugin implements a mechanism whereby actuators can be controlled
    in XMPP-based sensor networks, making it possible to integrate sensors
    and actuators of different brands, makes and models into larger
    Internet of Things applications.

    Also see <http://xmpp.org/extensions/xep-0325.html>

    Configuration Values:
        threaded -- Indicates if communication with sensors should be threaded.
                    Defaults to True.

    Events:
        Sensor side
        -----------
        Control Event:DirectSet    -- Received a control message
        Control Event:SetReq       -- Received a control request

        Client side
        -----------
        Control Event:SetResponse       -- Received a response to a
                                           control request, type result
        Control Event:SetResponseError  -- Received a response to a
                                           control request, type error

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
        set_request       -- Initiates a control request to modify data in
                             sensor(s). Non-blocking, a callback function will
                             be called when the sensor has responded.
        set_command       -- Initiates a control command to modify data in
                             sensor(s). Non-blocking. The sensor(s) will not
                             respond regardless of the result of the command,
                             so no callback is made.

    """

    name = 'xep_0325'
    description = 'XEP-0325 Internet of Things - Control'
    dependencies = set(['xep_0030'])
    stanza = stanza


    default_config = {
        'threaded': True
#        'session_db': None
    }

    def plugin_init(self):
        """ Start the XEP-0325 plugin """

        self.xmpp.register_handler(
                Callback('Control Event:DirectSet',
                    StanzaPath('message/set'),
                    self._handle_direct_set))

        self.xmpp.register_handler(
                Callback('Control Event:SetReq',
                    StanzaPath('iq@type=set/set'),
                    self._handle_set_req))

        self.xmpp.register_handler(
                Callback('Control Event:SetResponse',
                    StanzaPath('iq@type=result/setResponse'),
                    self._handle_set_response))

        self.xmpp.register_handler(
                Callback('Control Event:SetResponseError',
                    StanzaPath('iq@type=error/setResponse'),
                    self._handle_set_response))

        # Server side dicts
        self.nodes = {}
        self.sessions = {}

        self.last_seqnr = 0
        self.seqnr_lock = Lock()

        ## For testning only
        self.test_authenticated_from = ""

    def post_init(self):
        """ Init complete. Register our features in Serivce discovery. """
        BasePlugin.post_init(self)
        self.xmpp['xep_0030'].add_feature(Control.namespace)
        self.xmpp['xep_0030'].set_items(node=Control.namespace, items=tuple())

    def _new_session(self):
        """ Return a new session ID. """
        return str(time.time()) + '-' + self.xmpp.new_id()

    def plugin_end(self):
        """ Stop the XEP-0325 plugin """
        self.sessions.clear()
        self.xmpp.remove_handler('Control Event:DirectSet')
        self.xmpp.remove_handler('Control Event:SetReq')
        self.xmpp.remove_handler('Control Event:SetResponse')
        self.xmpp.remove_handler('Control Event:SetResponseError')
        self.xmpp['xep_0030'].del_feature(feature=Control.namespace)
        self.xmpp['xep_0030'].set_items(node=Control.namespace, items=tuple())


    # =================================================================
    # Sensor side (data provider) API

    def register_node(self, nodeId, device, commTimeout, sourceId=None, cacheType=None):
        """
        Register a sensor/device as available for control requests/commands
        through this XMPP instance.

        The device object may by any custom implementation to support
        specific devices, but it must implement the functions:
          has_control_field
          set_control_fields
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

    def _get_new_seqnr(self):
        """ Returns a unique sequence number (unique across threads) """
        self.seqnr_lock.acquire()
        self.last_seqnr += 1
        self.seqnr_lock.release()
        return str(self.last_seqnr)

    def _handle_set_req(self, iq):
        """
        Event handler for reception of an Iq with set req - this is a
        control request.

        Verifies that
          - all the requested nodes are available
            (if no nodes are specified in the request, assume all nodes)
          - all the control fields are available from all requested nodes
            (if no nodes are specified in the request, assume all nodes)

        If the request passes verification, the control request is passed
        to the devices (in a separate thread).
        If the verification fails, a setResponse with error indication
        is sent.
        """

        error_msg = ''
        req_ok = True
        missing_node = None
        missing_field = None

        # Authentication
        if len(self.test_authenticated_from) > 0 and not iq['from'] == self.test_authenticated_from:
            # Invalid authentication
            req_ok = False
            error_msg = "Access denied"

        # Nodes
        if len(iq['set']['nodes']) > 0:
            for n in iq['set']['nodes']:
                if not n['nodeId'] in self.nodes:
                    req_ok = False
                    missing_node = n['nodeId']
                    error_msg = "Invalid nodeId " + n['nodeId']
            process_nodes = [n['nodeId'] for n in iq['set']['nodes']]
        else:
            process_nodes = self.nodes.keys()

        # Fields - for control we need to find all in all devices, otherwise we reject
        process_fields = []
        if len(iq['set']['datas']) > 0:
            for f in iq['set']['datas']:
                for node in self.nodes:
                    if not self.nodes[node]["device"].has_control_field(f['name'], f._get_typename()):
                        req_ok = False
                        missing_field = f['name']
                        error_msg = "Invalid field " + f['name']
                        break
            process_fields = [(f['name'], f._get_typename(), f['value']) for f in iq['set']['datas']]

        if req_ok:
            session = self._new_session()
            self.sessions[session] = {"from": iq['from'], "to": iq['to'], "seqnr": iq['id']}
            self.sessions[session]["commTimers"] = {}
            self.sessions[session]["nodeDone"] = {}
            # Flag that a reply is exected when we are done
            self.sessions[session]["reply"] = True

            self.sessions[session]["node_list"] = process_nodes
            if self.threaded:
                #print("starting thread")
                tr_req = Thread(target=self._threaded_node_request, args=(session, process_fields))
                tr_req.start()
                #print("started thread")
            else:
                self._threaded_node_request(session, process_fields)

        else:
            iq.reply()
            iq['type'] = 'error'
            iq['setResponse']['responseCode'] = "NotFound"
            if missing_node is not None:
                iq['setResponse'].add_node(missing_node)
            if missing_field is not None:
                iq['setResponse'].add_data(missing_field)
            iq['setResponse']['error']['var'] = "Output"
            iq['setResponse']['error']['text'] = error_msg
            iq.send(block=False)

    def _handle_direct_set(self, msg):
        """
        Event handler for reception of a Message with set command - this is a
        direct control command.

        Verifies that
          - all the requested nodes are available
            (if no nodes are specified in the request, assume all nodes)
          - all the control fields are available from all requested nodes
            (if no nodes are specified in the request, assume all nodes)

        If the request passes verification, the control request is passed
        to the devices (in a separate thread).
        If the verification fails, do nothing.
        """
        req_ok = True

        # Nodes
        if len(msg['set']['nodes']) > 0:
            for n in msg['set']['nodes']:
                if not n['nodeId'] in self.nodes:
                    req_ok = False
                    error_msg = "Invalid nodeId " + n['nodeId']
            process_nodes = [n['nodeId'] for n in msg['set']['nodes']]
        else:
            process_nodes = self.nodes.keys()

        # Fields - for control we need to find all in all devices, otherwise we reject
        process_fields = []
        if len(msg['set']['datas']) > 0:
            for f in msg['set']['datas']:
                for node in self.nodes:
                    if not self.nodes[node]["device"].has_control_field(f['name'], f._get_typename()):
                        req_ok = False
                        missing_field = f['name']
                        error_msg = "Invalid field " + f['name']
                        break
            process_fields = [(f['name'], f._get_typename(), f['value']) for f in msg['set']['datas']]

        if req_ok:
            session = self._new_session()
            self.sessions[session] = {"from": msg['from'], "to": msg['to']}
            self.sessions[session]["commTimers"] = {}
            self.sessions[session]["nodeDone"] = {}
            self.sessions[session]["reply"] = False

            self.sessions[session]["node_list"] = process_nodes
            if self.threaded:
                #print("starting thread")
                tr_req = Thread(target=self._threaded_node_request, args=(session, process_fields))
                tr_req.start()
                #print("started thread")
            else:
                self._threaded_node_request(session, process_fields)


    def _threaded_node_request(self, session, process_fields):
        """
        Helper function to handle the device control in a separate thread.

        Arguments:
            session         -- The request session id
            process_fields  -- The fields to set in the devices. List of tuple format:
                               (name, datatype, value)
        """
        for node in self.sessions[session]["node_list"]:
            self.sessions[session]["nodeDone"][node] = False

        for node in self.sessions[session]["node_list"]:
            timer = Timer(self.nodes[node]['commTimeout'], self._event_comm_timeout, args=(session, node))
            self.sessions[session]["commTimers"][node] = timer
            timer.start()
            self.nodes[node]['device'].set_control_fields(process_fields, session=session, callback=self._device_set_command_callback)

    def _event_comm_timeout(self, session, nodeId):
        """
        Triggered if any of the control operations timeout.
        Stop communicating with the failing device.
        If the control command was an Iq request, sends a failure
        message back to the client.

        Arguments:
            session         -- The request session id
            nodeId          -- The id of the device which timed out
        """

        if self.sessions[session]["reply"]:
            # Reply is exected when we are done
            iq = self.xmpp.Iq()
            iq['from'] = self.sessions[session]['to']
            iq['to'] = self.sessions[session]['from']
            iq['type'] = "error"
            iq['id'] = self.sessions[session]['seqnr']
            iq['setResponse']['responseCode'] = "OtherError"
            iq['setResponse'].add_node(nodeId)
            iq['setResponse']['error']['var'] = "Output"
            iq['setResponse']['error']['text'] = "Timeout."
            iq.send(block=False)

        ## TODO - should we send one timeout per node??

        # Drop communication with this device and check if we are done
        self.sessions[session]["nodeDone"][nodeId] = True
        if (self._all_nodes_done(session)):
            # The session is complete, delete it
            del self.sessions[session]

    def _all_nodes_done(self, session):
        """
        Checks wheter all devices are done replying to the control command.

        Arguments:
            session         -- The request session id
        """
        for n in self.sessions[session]["nodeDone"]:
            if not self.sessions[session]["nodeDone"][n]:
                return False
        return True

    def _device_set_command_callback(self, session, nodeId, result, error_field=None, error_msg=None):
        """
        Callback function called by the devices when the control command is
        complete or failed.
        If needed, composes a message with the result and sends it back to the
        client.

        Arguments:
            session         -- The request session id
            nodeId          -- The device id which initiated the callback
            result          -- The current result status of the control command. Valid values are:
                               "error"  - Set fields failed.
                               "ok"     - All fields were set.
            error_field      -- [optional] Only applies when result == "error"
                                The field name that failed (usually means it is missing)
            error_msg        -- [optional] Only applies when result == "error".
                                Error details when a request failed.
        """

        if not session in self.sessions:
            # This can happend if a session was deleted, like in a timeout. Just drop the data.
            return

        if result == "error":
            self.sessions[session]["commTimers"][nodeId].cancel()

            if self.sessions[session]["reply"]:
                # Reply is exected when we are done
                iq = self.xmpp.Iq()
                iq['from'] = self.sessions[session]['to']
                iq['to'] = self.sessions[session]['from']
                iq['type'] = "error"
                iq['id'] = self.sessions[session]['seqnr']
                iq['setResponse']['responseCode'] = "OtherError"
                iq['setResponse'].add_node(nodeId)
                if error_field is not None:
                    iq['setResponse'].add_data(error_field)
                iq['setResponse']['error']['var'] = error_field
                iq['setResponse']['error']['text'] = error_msg
                iq.send(block=False)

                # Drop communication with this device and check if we are done
                self.sessions[session]["nodeDone"][nodeId] = True
                if (self._all_nodes_done(session)):
                    # The session is complete, delete it
                    del self.sessions[session]
        else:
            self.sessions[session]["commTimers"][nodeId].cancel()

            self.sessions[session]["nodeDone"][nodeId] = True
            if (self._all_nodes_done(session)):
                if self.sessions[session]["reply"]:
                    # Reply is exected when we are done
                    iq = self.xmpp.Iq()
                    iq['from'] = self.sessions[session]['to']
                    iq['to'] = self.sessions[session]['from']
                    iq['type'] = "result"
                    iq['id'] = self.sessions[session]['seqnr']
                    iq['setResponse']['responseCode'] = "OK"
                    iq.send(block=False)

                # The session is complete, delete it
                del self.sessions[session]


    # =================================================================
    # Client side (data controller) API

    def set_request(self, from_jid, to_jid, callback, fields, nodeIds=None):
        """
        Called on the client side to initiade a control request.
        Composes a message with the request and sends it to the device(s).
        Does not block, the callback will be called when the device(s)
        has responded.

        Arguments:
            from_jid        -- The jid of the requester
            to_jid          -- The jid of the device(s)
            callback        -- The callback function to call when data is availble.

                            The callback function must support the following arguments:

                from_jid    -- The jid of the responding device(s)
                result      -- The result of the control request. Valid values are:
                               "OK"             - Control request completed successfully
                               "NotFound"       - One or more nodes or fields are missing
                               "InsufficientPrivileges" - Not authorized.
                               "Locked"         - Field(s) is locked and cannot
                                                  be changed at the moment.
                               "NotImplemented" - Request feature not implemented.
                               "FormError"      - Error while setting with
                                                  a form (not implemented).
                               "OtherError"     - Indicates other types of
                                                  errors, such as timeout.
                                                  Details in the error_msg.


                nodeId      -- [optional] Only applicable when result == "error"
                               List of node Ids of failing device(s).

                fields      -- [optional] Only applicable when result == "error"
                               List of fields that failed.[optional] Mandatory when result == "rejected" or "failure".

                error_msg   -- Details about why the request failed.

            fields          -- Fields to set. List of tuple format: (name, typename, value).
            nodeIds         -- [optional] Limits the request to the node Ids in this list.
        """
        iq = self.xmpp.Iq()
        iq['from'] = from_jid
        iq['to'] = to_jid
        seqnr = self._get_new_seqnr()
        iq['id'] = seqnr
        iq['type'] = "set"
        if nodeIds is not None:
            for nodeId in nodeIds:
                iq['set'].add_node(nodeId)
        if fields is not None:
            for name, typename, value in fields:
                iq['set'].add_data(name=name, typename=typename, value=value)

        self.sessions[seqnr] = {"from": iq['from'], "to": iq['to'], "callback": callback}
        iq.send(block=False)

    def set_command(self, from_jid, to_jid, fields, nodeIds=None):
        """
        Called on the client side to initiade a control command.
        Composes a message with the set commandand sends it to the device(s).
        Does not block. Device(s) will not respond, regardless of result.

        Arguments:
            from_jid        -- The jid of the requester
            to_jid          -- The jid of the device(s)

            fields          -- Fields to set. List of tuple format: (name, typename, value).
            nodeIds         -- [optional] Limits the request to the node Ids in this list.
        """
        msg = self.xmpp.Message()
        msg['from'] = from_jid
        msg['to'] = to_jid
        msg['type'] = "set"
        if nodeIds is not None:
            for nodeId in nodeIds:
                msg['set'].add_node(nodeId)
        if fields is not None:
            for name, typename, value in fields:
                msg['set'].add_data(name, typename, value)

        # We won't get any reply, so don't create a session
        msg.send()

    def _handle_set_response(self, iq):
        """ Received response from device(s) """
        #print("ooh")
        seqnr = iq['id']
        from_jid = str(iq['from'])
        result = iq['setResponse']['responseCode']
        nodeIds = [n['name'] for n in iq['setResponse']['nodes']]
        fields = [f['name'] for f in iq['setResponse']['datas']]
        error_msg = None

        if not iq['setResponse'].find('error') is None and not iq['setResponse']['error']['text'] == "":
            error_msg = iq['setResponse']['error']['text']

        callback = self.sessions[seqnr]["callback"]
        callback(from_jid=from_jid, result=result, nodeIds=nodeIds, fields=fields, error_msg=error_msg)
