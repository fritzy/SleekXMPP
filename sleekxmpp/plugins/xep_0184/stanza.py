"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012 Erik Reuterborg Larsson, Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream.stanzabase import ElementBase, ET


class Request(ElementBase):
    namespace = 'urn:xmpp:receipts'
    name = 'request'
    plugin_attrib = 'request_reciept'
    interfaces = set(('request_reciept',))
    is_extension = True

    def setup(self, xml=None):
        self.xml = ET.Element('')
        return True

    def set_request_reciept(self, val):
        self.del_request_reciept()
        parent = self.parent()
        if val:
            self.xml = ET.Element("{%s}%s" % (self.namespace, self.name))
            parent.append(self.xml)

    def get_request_reciept(self):
        parent = self.parent()
        if parent.find("{%s}%s" % (self.namespace, self.name)) is not None:
            return True
        else:
            return False

    def del_request_reciept(self):
        self.xml = ET.Element('')


class Received(ElementBase):
    namespace = 'urn:xmpp:receipts'
    name = 'received'
    plugin_attrib = 'reciept_received'
    interfaces = set(('id',))
