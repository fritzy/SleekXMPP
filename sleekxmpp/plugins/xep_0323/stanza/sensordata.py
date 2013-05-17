"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Joachim Lindborg, Joachim.lindborg@lsys.se
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp import Iq, Message
from sleekxmpp.xmlstream import register_stanza_plugin, ElementBase, ET, JID


class Sensordata(ElementBase):
    namespace = 'http://xmpp.org/iot/sensordata'
    name = 'sensordata'
    plugin_attrib = name
    interfaces = set(tuple())

class Request(ElementBase):
    namespace = 'http://xmpp.org/iot/sensordata'
    name = 'req'
    plugin_attrib = name
    interfaces = set(('seqnr','momentary'))


class Accepted(ElementBase):
    namespace = 'http://xmpp.org/iot/sensordata'
    name = 'accepted'
    plugin_attrib = name
    interfaces = set(('seqnr'))


class Failure(ElementBase):
    namespace = 'http://xmpp.org/iot/sensordata'
    name = 'failure'
    plugin_attrib = name
    interfaces = set(('seqnr','done'))



register_stanza_plugin(Iq, Sensordata)
register_stanza_plugin(Sensordata, Request)
register_stanza_plugin(Sensordata, Accepted)
register_stanza_plugin(Sensordata, Failure)
# register_stanza_plugin(Pubsub, Default)
# register_stanza_plugin(Pubsub, Items)
# register_stanza_plugin(Pubsub, Options)
# register_stanza_plugin(Pubsub, Publish)
# register_stanza_plugin(Pubsub, PublishOptions)
# register_stanza_plugin(Pubsub, Retract)
# register_stanza_plugin(Pubsub, Subscribe)
# register_stanza_plugin(Pubsub, Subscription)
# register_stanza_plugin(Pubsub, Subscriptions)
# register_stanza_plugin(Pubsub, Unsubscribe)
# register_stanza_plugin(Affiliations, Affiliation, iterable=True)
# register_stanza_plugin(Configure, xep_0004.Form)
# register_stanza_plugin(Items, Item, iterable=True)
# register_stanza_plugin(Publish, Item, iterable=True)
# register_stanza_plugin(Retract, Item)
# register_stanza_plugin(Subscribe, Options)
# register_stanza_plugin(Subscription, SubscribeOptions)
# register_stanza_plugin(Subscriptions, Subscription, iterable=True)
