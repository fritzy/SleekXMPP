from sleekxmpp.xmlstream import ElementBase

class Action(ElementBase):
    name = 'action'
    namespace = 'sleekxmpp:custom:actions'
    plugin_attrib = 'action'
    interfaces = set(('method', 'param', 'status'))
    sub_interfaces = interfaces
