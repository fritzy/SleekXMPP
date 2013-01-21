"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ElementBase, register_stanza_plugin


class GmailQuery(ElementBase):
    namespace = 'google:mail:notify'
    name = 'query'
    plugin_attrib = 'gmail'
    interfaces = set(['newer_than_time', 'newer_than_tid', 'search'])

    def get_search(self):
        return self._get_attr('q', '')

    def set_search(self, search):
        self._set_attr('q', search)

    def del_search(self):
        self._del_attr('q')

    def get_newer_than_time(self):
        return self._get_attr('newer-than-time', '')

    def set_newer_than_time(self, value):
        self._set_attr('newer-than-time', value)

    def del_newer_than_time(self):
        self._del_attr('newer-than-time')

    def get_newer_than_tid(self):
        return self._get_attr('newer-than-tid', '')

    def set_newer_than_tid(self, value):
        self._set_attr('newer-than-tid', value)

    def del_newer_than_tid(self):
        self._del_attr('newer-than-tid')


class MailBox(ElementBase):
    namespace = 'google:mail:notify'
    name = 'mailbox'
    plugin_attrib = 'gmail_messages'
    interfaces = set(['result_time', 'url', 'matched', 'estimate'])

    def get_matched(self):
        return self._get_attr('total-matched', '')

    def get_estimate(self):
        return self._get_attr('total-estimate', '') == '1'

    def get_result_time(self):
        return self._get_attr('result-time', '')


class MailThread(ElementBase):
    namespace = 'google:mail:notify'
    name = 'mail-thread-info'
    plugin_attrib = 'thread'
    plugin_multi_attrib = 'threads'
    interfaces = set(['tid', 'participation', 'messages', 'date',
                      'senders', 'url', 'labels', 'subject', 'snippet'])
    sub_interfaces = set(['labels', 'subject', 'snippet'])

    def get_senders(self):
        result = []
        senders = self.xml.findall('{%s}senders/{%s}sender' % (
            self.namespace, self.namespace))

        for sender in senders:
            result.append(MailSender(xml=sender))

        return result


class MailSender(ElementBase):
    namespace = 'google:mail:notify'
    name = 'sender'
    plugin_attrib = name
    interfaces = set(['address', 'name', 'originator', 'unread'])

    def get_originator(self):
        return self.xml.attrib.get('originator', '0') == '1'

    def get_unread(self):
        return self.xml.attrib.get('unread', '0') == '1'


class NewMail(ElementBase):
    namespace = 'google:mail:notify'
    name = 'new-mail'
    plugin_attrib = 'gmail_notification'


register_stanza_plugin(MailBox, MailThread, iterable=True)
