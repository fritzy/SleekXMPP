"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

import sleekxmpp
from sleekxmpp.plugins.xep_0030 import StaticDisco


log = logging.getLogger(__name__)


class StaticExtendedDisco(object):

    """
    Extend the default StaticDisco implementation to provide
    support for extended identity information.
    """

    def __init__(self, static):
        """
        Augment the default XEP-0030 static handler object.

        Arguments:
            static -- The default static XEP-0030 handler object.
        """
        self.static = static

    def set_extended_info(self, jid, node, data):
        """
        Replace the extended identity data for a JID/node combination.

        The data parameter may provide:
            data -- Either a single data form, or a list of data forms.
        """
        self.del_extended_info(jid, node, data)
        self.add_extended_info(jid, node, data)

    def add_extended_info(self, jid, node, data):
        """
        Add additional extended identity data for a JID/node combination.

        The data parameter may provide:
            data -- Either a single data form, or a list of data forms.
        """
        self.static.add_node(jid, node)

        forms = data.get('data', [])
        if not isinstance(forms, list):
            forms = [forms]

        for form in forms:
            self.static.nodes[(jid, node)]['info'].append(form)

    def del_extended_info(self, jid, node, data):
        """
        Replace the extended identity data for a JID/node combination.

        The data parameter is not used.
        """
        if (jid, node) not in self.static.nodes:
            return

        info = self.static.nodes[(jid, node)]['info']

        for form in info['substanza']:
            info.xml.remove(form.xml)
