"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""
from xml.etree import cElementTree as ET
from . import base
import time
import logging


log = logging.getLogger(__name__)


class xep_0199(base.base_plugin):
    """XEP-0199 XMPP Ping"""

    def plugin_init(self):
        self.description = "XMPP Ping"
        self.xep = "0199"
        self.xmpp.add_handler("<iq type='get' xmlns='%s'><ping xmlns='urn:xmpp:ping'/></iq>" % self.xmpp.default_ns, self.handler_ping, name='XMPP Ping')
        if self.config.get('keepalive', True):
            self.xmpp.add_event_handler('session_start', self.handler_pingserver, threaded=True)

    def post_init(self):
        base.base_plugin.post_init(self)
        self.xmpp.plugin['xep_0030'].add_feature('urn:xmpp:ping')

    def handler_pingserver(self, xml):
        self.xmpp.schedule("xep-0119 ping", float(self.config.get('frequency', 300)), self.scheduled_ping, repeat=True)

    def scheduled_ping(self):
        log.debug("pinging...")
        if self.sendPing(self.xmpp.server, self.config.get('timeout', 30)) is False:
            log.debug("Did not recieve ping back in time.  Requesting Reconnect.")
            self.xmpp.reconnect()

    def handler_ping(self, xml):
        iq = self.xmpp.makeIqResult(xml.get('id', 'unknown'))
        iq.attrib['to'] = xml.get('from', self.xmpp.boundjid.domain)
        self.xmpp.send(iq)

    def sendPing(self, jid, timeout = 30):
        """ sendPing(jid, timeout)
        Sends a ping to the specified jid, returning the time (in seconds)
        to receive a reply, or None if no reply is received in timeout seconds.
        """
        id = self.xmpp.getNewId()
        iq = self.xmpp.makeIq(id)
        iq.attrib['type'] = 'get'
        iq.attrib['to'] = jid
        ping = ET.Element('{urn:xmpp:ping}ping')
        iq.append(ping)
        startTime = time.clock()
        #pingresult = self.xmpp.send(iq, self.xmpp.makeIq(id), timeout)
        pingresult = iq.send()
        endTime = time.clock()
        if pingresult == False:
            #self.xmpp.disconnect(reconnect=True)
            return False
        return endTime - startTime
