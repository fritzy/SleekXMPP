"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from datetime import datetime, tzinfo
import logging
import time

from . import base
from .. stanza.iq import Iq
from .. xmlstream.handler.callback import Callback
from .. xmlstream.matcher.xpath import MatchXPath
from .. xmlstream import ElementBase, ET, JID, register_stanza_plugin


log = logging.getLogger(__name__)


class EntityTime(ElementBase):
    name = 'time'
    namespace = 'urn:xmpp:time'
    plugin_attrib = 'entity_time'
    interfaces = set(('tzo', 'utc'))
    sub_interfaces = set(('tzo', 'utc'))

    #def get_utc(self): # TODO: return a datetime.tzinfo object?
        #pass

    def set_tzo(self, tzo): # TODO: support datetime.tzinfo objects?
        if isinstance(tzo, tzinfo):
            td = datetime.now(tzo).utcoffset() # What if we are faking the time? datetime.now() shouldn't be used here'
            seconds = td.seconds + td.days * 24 * 3600
            sign = ('+' if seconds >= 0 else '-')
            minutes = abs(seconds // 60)
            tzo = '{sign}{hours:02d}:{minutes:02d}'.format(sign=sign, hours=minutes//60, minutes=minutes%60)
        elif not isinstance(tzo, str):
            raise TypeError('The time should be a string or a datetime.tzinfo object.')
        self._set_sub_text('tzo', tzo)

    def get_utc(self):
        # Returns a datetime object instead the string. Is this a good idea?
        value = self._get_sub_text('utc')
        if '.' in value:
            return datetime.strptime(value, '%Y-%m-%d.%fT%H:%M:%SZ')
        else:
            return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')

    def set_utc(self, tim=None):
        if isinstance(tim, datetime):
            if tim.utcoffset():
                tim = tim - tim.utcoffset()
            tim = tim.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif isinstance(tim, time.struct_time):
            tim = time.strftime('%Y-%m-%dT%H:%M:%SZ', tim)
        elif not isinstance(tim, str):
            raise TypeError('The time should be a string or a datetime.datetime or time.struct_time object.')

        self._set_sub_text('utc', tim)


class xep_0202(base.base_plugin):
    """
    XEP-0202 Entity Time
    """
    def plugin_init(self):
        self.description = "Entity Time"
        self.xep = "0202"

        self.xmpp.registerHandler(
            Callback('Time Request',
                 MatchXPath('{%s}iq/{%s}time' % (self.xmpp.default_ns,
                                  EntityTime.namespace)),
                 self.handle_entity_time_query))
        register_stanza_plugin(Iq, EntityTime)

        self.xmpp.add_event_handler('entity_time_request', self.handle_entity_time)


    def post_init(self):
        base.base_plugin.post_init(self)

        self.xmpp.plugin['xep_0030'].add_feature('urn:xmpp:time')

    def handle_entity_time_query(self, iq):
        if iq['type'] == 'get':
            log.debug("Entity time requested by %s" % iq['from'])
            self.xmpp.event('entity_time_request', iq)
        elif iq['type'] == 'result':
            log.debug("Entity time result from %s" % iq['from'])
            self.xmpp.event('entity_time', iq)

    def handle_entity_time(self, iq):
        iq = iq.reply()
        iq.enable('entity_time')
        tzo = time.strftime('%z') # %z is not on all ANSI C libraries
        tzo = tzo[:3] + ':' + tzo[3:]
        iq['entity_time']['tzo'] = tzo
        iq['entity_time']['utc'] = datetime.utcnow()
        iq.send()

    def get_entity_time(self, jid):
        iq = self.xmpp.makeIqGet()
        iq.enable('entity_time')
        iq.attrib['to'] = jid
        iq.attrib['from'] = self.xmpp.boundjid.full
        id = iq.get('id')
        result = iq.send()
        if result and result is not None and result.get('type', 'error') != 'error':
            return {'utc': result['entity_time']['utc'], 'tzo': result['entity_time']['tzo']}
        else:
            return False
