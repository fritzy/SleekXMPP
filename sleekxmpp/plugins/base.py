"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""


class base_plugin(object):

    """
    The base_plugin class serves as a base for user created plugins
    that provide support for existing or experimental XEPS.

    Each plugin has a dictionary for configuration options, as well
    as a name and description.

    The lifecycle of a plugin is:
        1. The plugin is instantiated during registration.
        2. Once the XML stream begins processing, the method
           plugin_init() is called (if the plugin is configured
           as enabled with {'enable': True}).
        3. After all plugins have been initialized, the
           method post_init() is called.

    Recommended event handlers:
        session_start -- Plugins which require the use of the current
                         bound JID SHOULD wait for the session_start
                         event to perform any initialization (or
                         resetting). This is a transitive recommendation,
                         plugins that use other plugins which use the
                         bound JID should also wait for session_start
                         before making such calls.
        session_end   -- If the plugin keeps any per-session state,
                         such as joined MUC rooms, such state SHOULD
                         be cleared when the session_end event is raised.

    Attributes:
        xep          -- The XEP number the plugin implements, if any.
        description  -- A short description of the plugin, typically
                        the long name of the implemented XEP.
        xmpp         -- The main SleekXMPP instance.
        config       -- A dictionary of custom configuration values.
                        The value 'enable' is special and controls
                        whether or not the plugin is initialized
                        after registration.
        post_initted -- Executed after all plugins have been initialized
                        to handle any cross-plugin interactions, such as
                        registering service discovery items.
        enable       -- Indicates that the plugin is enabled for use and
                        will be initialized after registration.

    Methods:
        plugin_init  -- Initialize the plugin state.
        post_init    -- Handle any cross-plugin concerns.
    """

    def __init__(self, xmpp, config=None):
        """
        Instantiate a new plugin and store the given configuration.

        Arguments:
            xmpp   -- The main SleekXMPP instance.
            config -- A dictionary of configuration values.
        """
        if config is None:
            config = {}
        self.xep = None
        self.rfc = None
        self.description = 'Base Plugin'
        self.xmpp = xmpp
        self.config = config
        self.post_inited = False
        self.enable = config.get('enable', True)
        if self.enable:
            self.plugin_init()

    def plugin_init(self):
        """
        Initialize plugin state, such as registering any stream or
        event handlers, or new stanza types.
        """
        pass

    def post_init(self):
        """
        Perform any cross-plugin interactions, such as registering
        service discovery identities or items.
        """
        self.post_inited = True
