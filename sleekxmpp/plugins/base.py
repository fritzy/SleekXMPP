"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""


class base_plugin(object):

    def __init__(self, xmpp, config):
        self.xep = 'base'
        self.description = 'Base Plugin'
        self.xmpp = xmpp
        self.config = config
        self.post_inited = False
        self.enable = config.get('enable', True)
        if self.enable:
            self.plugin_init()

    def plugin_init(self):
        pass

    def post_init(self):
        self.post_inited = True
