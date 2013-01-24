"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ElementBase, ET


class GoogleAuth(ElementBase):
    name = 'use_full_bind_result'
    namespace = 'http://www.google.com/talk/protocol/auth'
    plugin_attrib = name
    interfaces = set([name])
    is_extension = True

    attribute = '{%s}client-users-full-bind-result' % namespace

    def setup(self, xml):
        """Don't create XML for the plugin."""
        self.xml = ET.Element('')

    def get_use_full_bind_result(self):
        return self.parent()._get_attr(self.attribute) == 'true'

    def set_use_full_bind_result(self, value):
        if value in (True, 'true'):
            self.parent()._set_attr(self.attribute, 'true')
        else:
            self.parent()._del_attr(self.attribute)

    def del_use_full_bind_result(self):
        self.parent()._del_attr(self.attribute)
