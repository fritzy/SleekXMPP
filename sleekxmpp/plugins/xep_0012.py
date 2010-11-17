"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from datetime import datetime
import logging

from . import base
from .. stanza.iq import Iq
from .. xmlstream.handler.callback import Callback
from .. xmlstream.matcher.xpath import MatchXPath
from .. xmlstream import ElementBase, ET, JID, register_stanza_plugin


log = logging.getLogger(__name__)


class LastActivity(ElementBase):
    name = 'query'
    namespace = 'jabber:iq:last'
    plugin_attrib = 'last_activity'
    interfaces = set(('seconds', 'status'))

    def get_seconds(self):
        return int(self._get_attr('seconds'))

    def set_seconds(self, value):
        self._set_attr('seconds', str(value))

    def get_status(self):
        return self.xml.text

    def set_status(self, value):
        self.xml.text = str(value)

    def del_status(self):
        self.xml.text = ''

class xep_0012(base.base_plugin):
    """
    XEP-0012 Last Activity
    """
    def plugin_init(self):
        self.description = "Last Activity"
        self.xep = "0012"

        self.xmpp.registerHandler(
            Callback('Last Activity',
                 MatchXPath('{%s}iq/{%s}query' % (self.xmpp.default_ns,
                                  LastActivity.namespace)),
                 self.handle_last_activity_query))
        register_stanza_plugin(Iq, LastActivity)

        self.xmpp.add_event_handler('last_activity_request', self.handle_last_activity)


    def post_init(self):
        base.base_plugin.post_init(self)
        if self.xmpp.is_component:
            # We are a component, so we track the uptime
            self.xmpp.add_event_handler("session_start", self._reset_uptime)
            self._start_datetime = datetime.now()
        self.xmpp.plugin['xep_0030'].add_feature('jabber:iq:last')

    def _reset_uptime(self, event):
        self._start_datetime = datetime.now()

    def handle_last_activity_query(self, iq):
        if iq['type'] == 'get':
            log.debug("Last activity requested by %s" % iq['from'])
            self.xmpp.event('last_activity_request', iq)
        elif iq['type'] == 'result':
            log.debug("Last activity result from %s" % iq['from'])
            self.xmpp.event('last_activity', iq)

    def handle_last_activity(self, iq):
        jid = iq['from']

        if self.xmpp.is_component:
            # Send the uptime
            result = LastActivity()
            td = (datetime.now() - self._start_datetime)
            result['seconds'] = td.seconds + td.days * 24 * 3600
            reply = iq.reply().setPayload(result.xml).send()
        else:
            barejid = JID(jid).bare
            if barejid in self.xmpp.roster and ( self.xmpp.roster[barejid]['subscription'] in ('from', 'both') or
                                                 barejid == self.xmpp.boundjid.bare ):
                # We don't know how to calculate it
                iq.reply().error().setPayload(iq['last_activity'].xml)
                iq['error']['code'] = '503'
                iq['error']['type'] = 'cancel'
                iq['error']['condition'] = 'service-unavailable'
                iq.send()
            else:
                iq.reply().error().setPayload(iq['last_activity'].xml)
                iq['error']['code'] = '403'
                iq['error']['type'] = 'auth'
                iq['error']['condition'] = 'forbidden'
                iq.send()

    def get_last_activity(self, jid):
        """Query the LastActivity of jid and return it in seconds"""
        iq = self.xmpp.makeIqGet()
        query = LastActivity()
        iq.append(query.xml)
        iq.attrib['to'] = jid
        iq.attrib['from'] = self.xmpp.boundjid.full
        id = iq.get('id')
        result = iq.send()
        if result and result is not None and result.get('type', 'error') != 'error':
            return result['last_activity']['seconds']
        else:
            return False
