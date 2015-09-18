"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging
import socket
import zlib

from sleekxmpp.thirdparty.suelta.util import bytes


from sleekxmpp.stanza import StreamFeatures
from sleekxmpp.xmlstream import RestartStream, register_stanza_plugin, ElementBase, StanzaBase
from sleekxmpp.xmlstream.matcher import *
from sleekxmpp.xmlstream.handler import *
from sleekxmpp.plugins import BasePlugin, register_plugin

log = logging.getLogger(__name__)


class Compression(ElementBase):
    name = 'compression'
    namespace = 'http://jabber.org/features/compress'
    interfaces = set(('methods',))
    plugin_attrib = 'compression'
    plugin_tag_map = {}
    plugin_attrib_map = {}

    def get_methods(self):
        methods = []
        for method in self.xml.findall('{%s}method' % self.namespace):
            methods.append(method.text)
        return methods


class Compress(StanzaBase):
    name = 'compress'
    namespace = 'http://jabber.org/protocol/compress'
    interfaces = set(('method',))
    sub_interfaces = interfaces
    plugin_attrib = 'compress'
    plugin_tag_map = {}
    plugin_attrib_map = {}

    def setup(self, xml):
        StanzaBase.setup(self, xml)
        self.xml.tag = self.tag_name()


class Compressed(StanzaBase):
    name = 'compressed'
    namespace = 'http://jabber.org/protocol/compress'
    interfaces = set()
    plugin_tag_map = {}
    plugin_attrib_map = {}

    def setup(self, xml):
        StanzaBase.setup(self, xml)
        self.xml.tag = self.tag_name()




class ZlibSocket(object):

    def __init__(self, socketobj):
        self.__socket = socketobj
        self.compressor = zlib.compressobj()
        self.decompressor = zlib.decompressobj(zlib.MAX_WBITS)

    def __getattr__(self, name):
        return getattr(self.__socket, name)

    def send(self, data):
        sentlen = len(data)
        data = self.compressor.compress(data)
        data += self.compressor.flush(zlib.Z_SYNC_FLUSH)
        log.debug(b'>>> (compressed)' + (data.encode("hex")))
        #return self.__socket.send(data)
        sentactuallen = self.__socket.send(data)
        assert(sentactuallen == len(data))

        return sentlen

    def recv(self, *args, **kwargs):
        data = self.__socket.recv(*args, **kwargs)
        log.debug(b'<<< (compressed)' + data.encode("hex"))
        return self.decompressor.decompress(self.decompressor.unconsumed_tail + data)


class XEP_0138(BasePlugin):
    """
    XEP-0138: Compression
    """
    name = "xep_0138"
    description = "XEP-0138: Compression"
    dependencies = set(["xep_0030"])

    def plugin_init(self):
        self.xep = '0138'
        self.description = 'Stream Compression (Generic)'

        self.compression_methods = {'zlib': True}

        register_stanza_plugin(StreamFeatures, Compression)
        self.xmpp.register_stanza(Compress)
        self.xmpp.register_stanza(Compressed)

        self.xmpp.register_handler(
                Callback('Compressed',
                    StanzaPath('compressed'),
                    self._handle_compressed,
                    instream=True))

        self.xmpp.register_feature('compression',
                self._handle_compression,
                restart=True,
                order=self.config.get('order', 5))

    def register_compression_method(self, name, handler):
        self.compression_methods[name] = handler

    def _handle_compression(self, features):
        for method in features['compression']['methods']:
            if method in self.compression_methods:
                log.info('Attempting to use %s compression' % method)
                c = Compress(self.xmpp)
                c['method'] = method
                c.send(now=True)
                return True
        return False

    def _handle_compressed(self, stanza):
        self.xmpp.features.add('compression')
        log.debug('Stream Compressed!')
        compressed_socket = ZlibSocket(self.xmpp.socket)
        self.xmpp.set_socket(compressed_socket)
        raise RestartStream()

    def _handle_failure(self, stanza):
        pass

xep_0138 = XEP_0138
register_plugin(XEP_0138)
