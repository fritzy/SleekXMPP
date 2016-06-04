"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of Message Processing Hints
    http://xmpp.org/extensions/xep-0334.html
    Copyright (C) 2016 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import ElementBase

class Store(ElementBase):
    name = 'store'
    plugin_attrib = 'store'
    namespace = 'urn:xmpp:hints'

class NoPermanentStore(ElementBase):
    name = 'no-permanent-store'
    plugin_attrib = 'no-permanent-store'
    namespace = 'urn:xmpp:hints'

class NoStore(ElementBase):
    name = 'no-store'
    plugin_attrib = 'no-store'
    namespace = 'urn:xmpp:hints'

class NoCopy(ElementBase):
    name = 'no-copy'
    plugin_attrib = 'no-copy'
    namespace = 'urn:xmpp:hints'
