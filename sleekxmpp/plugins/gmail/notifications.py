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
from sleekxmpp.plugins.gmail import stanza


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
                Callback('Gmail Result',
                    MatchXPath('{%s}iq/{%s}%s' % (
                        self.xmpp.default_ns,
                        stanza.MailBox.namespace,
                        stanza.MailBox.name)),
                    self._handle_gmail))

        self.xmpp.register_handler(
                Callback('Gmail New Mail',
                    MatchXPath('{%s}iq/{%s}%s' % (
                        self.xmpp.default_ns,
                        stanza.NewMail.namespace,
                        stanza.NewMail.name)),
                    self._handle_new_mail))

        self._last_result_time = None

    def plugin_end(self):
        self.xmpp.remove_handler('Gmail Result')
        self.xmpp.remove_handler('Gmail New Mail')

    def _handle_gmail(self, iq):
        mailbox = iq['gmail_results']
        log.info('Gmail: Received%s %s emails',
                ' approximately' if mailbox['estimated'] else '',
                mailbox['matched'])
        self._last_result_time = mailbox['result_time']
        self.xmpp.event('gmail_messages', iq)

    def _handle_new_mail(self, iq):
        log.info("Gmail: New emails received!")
        self.xmpp.event('gmail_notify', iq)
        self.check(block=False)

    def check(self, block=True, timeout=None, callback=None):
        return self.search(newer=self._last_result_time,
                block=block,
                timeout=timeout,
                callback=callback)

    def search(self, query=None, newer=None, block=True,
                     timeout=None, callback=None):
        if not query:
            log.info('Gmail: Checking for new email')
        else:
            log.info('Gmail: Searching for emails matching: "%s"', query)
        iq = self.xmpp.Iq()
        iq['type'] = 'get'
        iq['to'] = self.xmpp.boundjid.bare
        iq['gmail']['search'] = query
        iq['gmail']['newer_than_time'] = newer
        return iq.send(block=block, timeout=timeout, callback=callback)
