from sleekxmpp.jid import JID
from sleekxmpp.xmlstream import ElementBase, register_stanza_plugin


class Socks5(ElementBase):
    name = 'query'
    namespace = 'http://jabber.org/protocol/bytestreams'
    plugin_attrib = 'socks'
    interfaces = set(['sid', 'activate'])
    sub_interfaces = set(['activate'])

    def add_streamhost(self, jid, host, port):
        sh = StreamHost(parent=self)
        sh['jid'] = jid
        sh['host'] = host
        sh['port'] = port


class StreamHost(ElementBase):
    name = 'streamhost'
    namespace = 'http://jabber.org/protocol/bytestreams'
    plugin_attrib = 'streamhost'
    plugin_multi_attrib = 'streamhosts'
    interfaces = set(['host', 'jid', 'port'])

    def set_jid(self, value):
        return self._set_attr('jid', str(value))

    def get_jid(self):
        return JID(self._get_attr('jid'))


class StreamHostUsed(ElementBase):
    name = 'streamhost-used'
    namespace = 'http://jabber.org/protocol/bytestreams'
    plugin_attrib = 'streamhost_used'
    interfaces = set(['jid'])

    def set_jid(self, value):
        return self._set_attr('jid', str(value))

    def get_jid(self):
        return JID(self._get_attr('jid'))


register_stanza_plugin(Socks5, StreamHost, iterable=True)
register_stanza_plugin(Socks5, StreamHostUsed)
