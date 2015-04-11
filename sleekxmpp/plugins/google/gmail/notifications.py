"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

from sleekxmpp.stanza import Iq
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import MatchXPath
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.plugins.google.gmail import stanza


log = logging.getLogger(__name__)


class Gmail(BasePlugin):

    """
    Google: Gmail Notifications

    Also see <https://developers.google.com/talk/jep_extensions/gmail>.
    """

    name = 'gmail'
    description = 'Google: Gmail Notifications'
    dependencies = set()
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Iq, stanza.GmailQuery)
        register_stanza_plugin(Iq, stanza.MailBox)
        register_stanza_plugin(Iq, stanza.NewMail)

        self.xmpp.register_handler(
                Callback('Gmail New Mail',
                    MatchXPath('{%s}iq/{%s}%s' % (
                        self.xmpp.default_ns,
                        stanza.NewMail.namespace,
                        stanza.NewMail.name)),
                    self._handle_new_mail))

        self._last_result_time = None
        self._last_result_tid = None

    def plugin_end(self):
        self.xmpp.remove_handler('Gmail New Mail')

    def _handle_new_mail(self, iq):
        log.info('Gmail: New email!')
        iq.reply().send()
        self.xmpp.event('gmail_notification')

    def check(self, block=True, timeout=None, callback=None):
        last_time = self._last_result_time
        last_tid = self._last_result_tid

        if not block:
            callback = lambda iq: self._update_last_results(iq, callback)

        resp = self.search(newer_time=last_time,
            newer_tid=last_tid,
            block=block,
            timeout=timeout,
            callback=callback)

        if block:
            self._update_last_results(resp)
            return resp

    def _update_last_results(self, iq, callback=None):
        self._last_result_time = iq['gmail_messages']['result_time']
        threads = iq['gmail_messages']['threads']
        if threads:
            self._last_result_tid = threads[0]['tid']
        if callback:
            callback(iq)

    def search(self, query=None, newer_time=None, newer_tid=None, block=True,
                     timeout=None, callback=None):
        if not query:
            log.info('Gmail: Checking for new email')
        else:
            log.info('Gmail: Searching for emails matching: "%s"', query)
        iq = self.xmpp.Iq()
        iq['type'] = 'get'
        iq['to'] = self.xmpp.boundjid.bare
        iq['gmail']['search'] = query
        iq['gmail']['newer_than_time'] = newer_time
        iq['gmail']['newer_than_tid'] = newer_tid
        return iq.send(block=block, timeout=timeout, callback=callback)
