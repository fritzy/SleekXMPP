from sleekxmpp.xmlstream.stanzabase import registerStanzaPlugin, ElementBase, ET, JID
from sleekxmpp.stanza.iq import Iq
from sleekxmpp.stanza.message import Message
from sleekxmpp.basexmpp import basexmpp
from sleekxmpp.xmlstream.xmlstream import XMLStream
import logging
from sleekxmpp.plugins import xep_0004
from sleekxmpp.plugins.xep_0060.stanza.base import OptionalSetting


class Pubsub(ElementBase):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'pubsub'
    plugin_attrib = 'pubsub'
    interfaces = set(tuple())
    plugin_attrib_map = {}
    plugin_tag_map = {}

registerStanzaPlugin(Iq, Pubsub)


class Affiliation(ElementBase):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'affiliation'
    plugin_attrib = name
    interfaces = set(('node', 'affiliation', 'jid'))
    plugin_attrib_map = {}
    plugin_tag_map = {}

    def setJid(self, value):
        self._setAttr('jid', str(value))

    def getJid(self):
        return JID(self._getAttr('jid'))

class Affiliations(ElementBase):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'affiliations'
    plugin_attrib = 'affiliations'
    interfaces = set(tuple())
    plugin_attrib_map = {}
    plugin_tag_map = {}
    subitem = (Affiliation,)

registerStanzaPlugin(Pubsub, Affiliations)


class Subscription(ElementBase):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'subscription'
    plugin_attrib = name
    interfaces = set(('jid', 'node', 'subscription', 'subid'))
    plugin_attrib_map = {}
    plugin_tag_map = {}

    def setjid(self, value):
        self._setattr('jid', str(value))

    def getjid(self):
        return jid(self._getattr('jid'))

registerStanzaPlugin(Pubsub, Subscription)

class Subscriptions(ElementBase):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'subscriptions'
    plugin_attrib = 'subscriptions'
    interfaces = set(tuple())
    plugin_attrib_map = {}
    plugin_tag_map = {}
    subitem = (Subscription,)

registerStanzaPlugin(Pubsub, Subscriptions)


class SubscribeOptions(ElementBase, OptionalSetting):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'subscribe-options'
    plugin_attrib = 'suboptions'
    plugin_attrib_map = {}
    plugin_tag_map = {}
    interfaces = set(('required',))

registerStanzaPlugin(Subscription, SubscribeOptions)

class Item(ElementBase):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'item'
    plugin_attrib = name
    interfaces = set(('id', 'payload'))
    plugin_attrib_map = {}
    plugin_tag_map = {}

    def setPayload(self, value):
        del self['payload']
        self.append(value)

    def getPayload(self):
        childs = self.xml.getchildren()
        if len(childs) > 0:
            return childs[0]

    def delPayload(self):
        for child in self.xml.getchildren():
            self.xml.remove(child)

class Items(ElementBase):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'items'
    plugin_attrib = 'items'
    interfaces = set(('node', 'max_items'))
    plugin_attrib_map = {}
    plugin_tag_map = {}
    subitem = (Item,)

registerStanzaPlugin(Pubsub, Items)

class Create(ElementBase):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'create'
    plugin_attrib = name
    interfaces = set(('node',))
    plugin_attrib_map = {}
    plugin_tag_map = {}

registerStanzaPlugin(Pubsub, Create)

#class Default(ElementBase):
#    namespace = 'http://jabber.org/protocol/pubsub'
#    name = 'default'
#    plugin_attrib = name
#    interfaces = set(('node', 'type'))
#    plugin_attrib_map = {}
#    plugin_tag_map = {}
#
#    def getType(self):
#        t = self._getAttr('type')
#        if not t: t == 'leaf'
#        return t
#
#registerStanzaPlugin(Pubsub, Default)

class Publish(Items):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'publish'
    plugin_attrib = name
    interfaces = set(('node',))
    plugin_attrib_map = {}
    plugin_tag_map = {}
    subitem = (Item,)

registerStanzaPlugin(Pubsub, Publish)

class Retract(ElementBase):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'retract'
    plugin_attrib = name
    interfaces = set(('node', 'notify'))
    plugin_attrib_map = {}
    plugin_tag_map = {}

registerStanzaPlugin(Pubsub, Retract)
registerStanzaPlugin(Retract, Item)

class Unsubscribe(ElementBase):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'unsubscribe'
    plugin_attrib = name
    interfaces = set(('node', 'jid', 'subid'))
    plugin_attrib_map = {}
    plugin_tag_map = {}

    def setJid(self, value):
        self._setAttr('jid', str(value))

    def getJid(self):
        return JID(self._getAttr('jid'))

registerStanzaPlugin(Pubsub, Unsubscribe)

class Subscribe(ElementBase):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'subscribe'
    plugin_attrib = name
    interfaces = set(('node', 'jid'))
    plugin_attrib_map = {}
    plugin_tag_map = {}

    def setJid(self, value):
        self._setAttr('jid', str(value))

    def getJid(self):
        return JID(self._getAttr('jid'))

registerStanzaPlugin(Pubsub, Subscribe)

class Configure(ElementBase):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'configure'
    plugin_attrib = name
    interfaces = set(('node', 'type'))
    plugin_attrib_map = {}
    plugin_tag_map = {}

    def getType(self):
        t = self._getAttr('type')
        if not t: t == 'leaf'
        return t

registerStanzaPlugin(Pubsub, Configure)
registerStanzaPlugin(Configure, xep_0004.Form)

class Options(ElementBase):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'options'
    plugin_attrib = 'options'
    interfaces = set(('jid', 'node', 'options'))
    plugin_attrib_map = {}
    plugin_tag_map = {}

    def __init__(self, *args, **kwargs):
        ElementBase.__init__(self, *args, **kwargs)

    def getOptions(self):
        config = self.xml.find('{jabber:x:data}x')
        form = xep_0004.Form(xml=config)
        return form

    def setOptions(self, value):
        self.xml.append(value.getXML())
        return self

    def delOptions(self):
        config = self.xml.find('{jabber:x:data}x')
        self.xml.remove(config)

    def setJid(self, value):
        self._setAttr('jid', str(value))

    def getJid(self):
        return JID(self._getAttr('jid'))

registerStanzaPlugin(Pubsub, Options)
registerStanzaPlugin(Subscribe, Options)

class PublishOptions(ElementBase):
    namespace = 'http://jabber.org/protocol/pubsub'
    name = 'publish-options'
    plugin_attrib = 'publish_options'
    interfaces = set(('publish_options',))
    is_extension = True
    plugin_attrib_map = {}
    plugin_tag_map = {}

    def get_publish_options(self):
        config = self.xml.find('{jabber:x:data}x')
        if config is None:
            return None
        form = xep_0004.Form(xml=config)
        return form

    def set_publish_options(self, value):
        if value is None:
            self.del_publish_options()
        else:
            self.xml.append(value.getXML())
        return self

    def del_publish_options(self):
        config = self.xml.find('{jabber:x:data}x')
        if config is not None:
            self.xml.remove(config)
        self.parent().xml.remove(self.xml)

registerStanzaPlugin(Pubsub, PublishOptions)

class PubsubState(ElementBase):
    namespace = 'http://jabber.org/protocol/psstate'
    name = 'state'
    plugin_attrib = 'psstate'
    interfaces = set(('node', 'item', 'payload'))
    plugin_attrib_map = {}
    plugin_tag_map = {}

    def setPayload(self, value):
        self.xml.append(value)

    def getPayload(self):
        childs = self.xml.getchildren()
        if len(childs) > 0:
            return childs[0]

    def delPayload(self):
        for child in self.xml.getchildren():
            self.xml.remove(child)

registerStanzaPlugin(Iq, PubsubState)

class PubsubStateEvent(ElementBase):
    namespace = 'http://jabber.org/protocol/psstate#event'
    name = 'event'
    plugin_attrib = 'psstate_event'
    intefaces = set(tuple())
    plugin_attrib_map = {}
    plugin_tag_map = {}

registerStanzaPlugin(Message, PubsubStateEvent)
registerStanzaPlugin(PubsubStateEvent, PubsubState)
