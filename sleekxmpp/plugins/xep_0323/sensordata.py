"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Joachim Lindborg, Joachim.lindborg@lsys.se
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.xmlstream import JID
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.plugins.base import BasePlugin
from sleekxmpp.plugins.xep_0323 import stanza


log = logging.getLogger(__name__)


class XEP_0323(BasePlugin):

    """
    XEP-0323 IoT Sensor Data 
    """

    name = 'xep_0323'
    description = 'XEP-0323 Internet of Things - Sensor Data'
    dependencies = set(['xep_0030']) # set(['xep_0030', 'xep_0004', 'xep_0082', 'xep_0131'])
    stanza = stanza

    def plugin_init(self):
        pass
        # self.node_event_map = {}

        # self.xmpp.register_handler(
        #        Callback('Sensordata Event: Get',
        #            StanzaPath('message/sensordata_event/get'),
        #            self._handle_event_get))

    def plugin_end(self):
        # self.xmpp.remove_handler('Sensordata Event: Get')
        pass
    
    def get_value(self, jid, msg):
        """
        Recieving a stanza for erading values
        # verify provisioning

        # verify requested values and categories

        # Send accepted
        # Thread of the readout

        # send started

        # send data messages

        # send done  
        """        
        pass
    

