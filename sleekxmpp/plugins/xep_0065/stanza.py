from sleekxmpp.xmlstream import ElementBase

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


class Query(ElementBase):
    """ The query xml element.
    """

    namespace = namespace
    name = 'query'
    plugin_attrib = 'q'
    interfaces = set(('sid', 'activate'))
    sub_interfaces = set(('activate',))



