"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from __future__ import absolute_import

import logging
import base64
import sys
import hashlib

from sleekxmpp import plugins
from sleekxmpp import stanza
from sleekxmpp.basexmpp import BaseXMPP
from sleekxmpp.xmlstream import XMLStream, RestartStream
from sleekxmpp.xmlstream import StanzaBase, ET
from sleekxmpp.xmlstream.matcher import *
from sleekxmpp.xmlstream.handler import *


log = logging.getLogger(__name__)


class ComponentXMPP(BaseXMPP):

    """
    SleekXMPP's basic XMPP server component.

    Use only for good, not for evil.

    Methods:
        connect              -- Overrides XMLStream.connect.
        incoming_filter      -- Overrides XMLStream.incoming_filter.
        start_stream_handler -- Overrides XMLStream.start_stream_handler.
    """

    def __init__(self, jid, secret, host, port,
                 plugin_config={}, plugin_whitelist=[], use_jc_ns=False):
        """
        Arguments:
            jid              -- The JID of the component.
            secret           -- The secret or password for the component.
            host             -- The server accepting the component.
            port             -- The port used to connect to the server.
            plugin_config    -- A dictionary of plugin configurations.
            plugin_whitelist -- A list of desired plugins to load
                                when using register_plugins.
            use_js_ns        -- Indicates if the 'jabber:client' namespace
                                should be used instead of the standard
                                'jabber:component:accept' namespace.
                                Defaults to False.
        """
        if use_jc_ns:
            default_ns = 'jabber:client'
        else:
            default_ns = 'jabber:component:accept'
        BaseXMPP.__init__(self, default_ns)

        self.auto_authorize = None
        self.stream_header = "<stream:stream %s %s to='%s'>" % (
                'xmlns="jabber:component:accept"',
                'xmlns:stream="%s"' % self.stream_ns,
                jid)
        self.stream_footer = "</stream:stream>"
        self.server_host = host
        self.server_port = port
        self.set_jid(jid)
        self.secret = secret
        self.plugin_config = plugin_config
        self.plugin_whitelist = plugin_whitelist
        self.is_component = True

        self.register_handler(
                Callback('Handshake',
                         MatchXPath('{jabber:component:accept}handshake'),
                         self._handle_handshake))

    def connect(self):
        """
        Connect to the server.

        Overrides XMLStream.connect.
        """
        log.debug("Connecting to %s:%s" % (self.server_host,
                                               self.server_port))
        return XMLStream.connect(self, self.server_host,
                                       self.server_port)

    def incoming_filter(self, xml):
        """
        Pre-process incoming XML stanzas by converting any 'jabber:client'
        namespaced elements to the component's default namespace.

        Overrides XMLStream.incoming_filter.

        Arguments:
            xml -- The XML stanza to pre-process.
        """
        if xml.tag.startswith('{jabber:client}'):
            xml.tag = xml.tag.replace('jabber:client', self.default_ns)

        # The incoming_filter call is only made on top level stanza
        # elements. So we manually continue filtering on sub-elements.
        for sub in xml:
            self.incoming_filter(sub)

        return xml

    def start_stream_handler(self, xml):
        """
        Once the streams are established, attempt to handshake
        with the server to be accepted as a component.

        Overrides XMLStream.start_stream_handler.

        Arguments:
            xml -- The incoming stream's root element.
        """
        # Construct a hash of the stream ID and the component secret.
        sid = xml.get('id', '')
        pre_hash = '%s%s' % (sid, self.secret)
        if sys.version_info >= (3, 0):
            # Handle Unicode byte encoding in Python 3.
            pre_hash = bytes(pre_hash, 'utf-8')

        handshake = ET.Element('{jabber:component:accept}handshake')
        handshake.text = hashlib.sha1(pre_hash).hexdigest().lower()
        self.send_xml(handshake)

    def _handle_handshake(self, xml):
        """
        The handshake has been accepted.

        Arguments:
            xml -- The reply handshake stanza.
        """
        self.event("session_start")
