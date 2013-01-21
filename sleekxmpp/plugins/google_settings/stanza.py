"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ET, ElementBase, register_stanza_plugin


class UserSettings(ElementBase):
    name = 'usersetting'
    namespace = 'google:setting'
    plugin_attrib = 'google_settings'
    interfaces = set(['auto_accept_suggestions',
                      'mail_notifications',
                      'archiving_enabled',
                      'gmail',
                      'email_verified',
                      'domain_privacy_notice',
                      'display_name'])

    def _get_setting(self, setting):
        xml = self.xml.find('{%s}%s' % (self.namespace, setting))
        if xml is not None:
            return xml.attrib.get('value', '') == 'true'
        return False

    def _set_setting(self, setting, value):
        self._del_setting(setting)
        if value in (True, False):
            xml = ET.Element('{%s}%s' % (self.namespace, setting))
            xml.attrib['value'] = 'true' if value else 'false'
            self.xml.append(xml)

    def _del_setting(self, setting):
        xml = self.xml.find('{%s}%s' % (self.namespace, setting))
        if xml is not None:
            self.xml.remove(xml)

    def get_display_name(self):
        xml = self.xml.find('{%s}%s' % (self.namespace, 'displayname'))
        if xml is not None:
            return xml.attrib.get('value', '')
        return ''

    def set_display_name(self, value):
        self._del_setting(setting)
        if value:
            xml = ET.Element('{%s}%s' % (self.namespace, 'displayname'))
            xml.attrib['value'] = value
            self.xml.append(xml)

    def del_display_name(self):
        self._del_setting('displayname')

    def get_auto_accept_suggestions(self):
        return self._get_setting('autoacceptsuggestions')

    def get_mail_notifications(self):
        return self._get_setting('mailnotifications')

    def get_archiving_enabled(self):
        return self._get_setting('archivingenabled')

    def get_gmail(self):
        return self._get_setting('gmail')

    def get_email_verified(self):
        return self._get_setting('emailverified')

    def get_domain_privacy_notice(self):
        return self._get_setting('domainprivacynotice')

    def set_auto_accept_suggestions(self, value):
        self._set_setting('autoacceptsuggestions', value)

    def set_mail_notifications(self, value):
        self._set_setting('mailnotifications', value)

    def set_archiving_enabled(self, value):
        self._set_setting('archivingenabled', value)

    def set_gmail(self, value):
        self._set_setting('gmail', value)

    def set_email_verified(self, value):
        self._set_setting('emailverified', value)

    def set_domain_privacy_notice(self, value):
        self._set_setting('domainprivacynotice', value)

    def del_auto_accept_suggestions(self):
        self._del_setting('autoacceptsuggestions')

    def del_mail_notifications(self):
        self._del_setting('mailnotifications')

    def del_archiving_enabled(self):
        self._del_setting('archivingenabled')

    def del_gmail(self):
        self._del_setting('gmail')

    def del_email_verified(self):
        self._del_setting('emailverified')

    def del_domain_privacy_notice(self):
        self._del_setting('domainprivacynotice')
