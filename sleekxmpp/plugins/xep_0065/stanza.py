from sleekxmpp import Iq
from sleekxmpp.xmlstream import ElementBase, register_stanza_plugin


# The protocol namespace defined in the Socks5Bytestream (0065) spec.
namespace = 'http://jabber.org/protocol/bytestreams'


class StreamHost(ElementBase):
    """ The streamhost xml element.
    """

    namespace = namespace
    name = 'streamhost'
    plugin_attrib = 'streamhost'
    interfaces = set(('host', 'jid', 'port'))


class StreamHostUsed(ElementBase):
    """ The streamhost-used xml element.
    """

    namespace = namespace
    name = 'streamhost-used'
    plugin_attrib = 'streamhost-used'
    interfaces = set(('jid',))


class Socks5(ElementBase):
    """ The query xml element.
    """

    namespace = namespace
    name = 'query'
    plugin_attrib = 'socks'
    interfaces = set(('sid', 'activate'))
    sub_interfaces = set(('activate',))

register_stanza_plugin(Iq, Socks5)
register_stanza_plugin(Socks5, StreamHost)
register_stanza_plugin(Socks5, StreamHostUsed)
