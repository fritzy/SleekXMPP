"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""


class JID(object):
    """
    A representation of a Jabber ID, or JID.

    Each JID may have three components: a user, a domain, and an optional
    resource. For example: user@domain/resource

    When a resource is not used, the JID is called a bare JID.
    The JID is a full JID otherwise.

    Attributes:
        jid      -- Alias for 'full'.
        full     -- The value of the full JID.
        bare     -- The value of the bare JID.
        user     -- The username portion of the JID.
        domain   -- The domain name portion of the JID.
        server   -- Alias for 'domain'.
        resource -- The resource portion of the JID.

    Methods:
        reset      -- Use a new JID value.
        regenerate -- Recreate the JID from its components.
    """

    def __init__(self, jid):
        """Initialize a new JID"""
        self.reset(jid)

    def reset(self, jid):
        """
        Start fresh from a new JID string.

        Arguments:
            jid - The new JID value.
        """
        self._full = self._jid = str(jid)
        self._domain = None
        self._resource = None
        self._user = None
        self._bare = None

    def __getattr__(self, name):
        """
        Handle getting the JID values, using cache if available.

        Arguments:
            name -- One of: user, server, domain, resource,
                    full, or bare.
        """
        if name == 'resource':
            if self._resource is None and '/' in self._jid:
                self._resource = self._jid.split('/', 1)[-1]
            return self._resource or ""
        elif name == 'user':
            if self._user is None:
                if '@' in self._jid:
                    self._user = self._jid.split('@', 1)[0]
                else:
                    self._user = self._user
            return self._user or ""
        elif name in ('server', 'domain', 'host'):
            if self._domain is None:
                self._domain = self._jid.split('@', 1)[-1].split('/', 1)[0]
            return self._domain or ""
        elif name == 'full':
            return self._jid or ""
        elif name == 'bare':
            if self._bare is None:
                self._bare = self._jid.split('/', 1)[0]
            return self._bare or ""

    def __setattr__(self, name, value):
        """
        Edit a JID by updating it's individual values, resetting the
        generated JID in the end.

        Arguments:
            name  -- The name of the JID part. One of: user, domain,
                     server, resource, full, jid, or bare.
            value -- The new value for the JID part.
        """
        if name in ('resource', 'user', 'domain'):
            object.__setattr__(self, "_%s" % name, value)
            self.regenerate()
        elif name in ('server', 'domain', 'host'):
            self.domain = value
        elif name in ('full', 'jid'):
            self.reset(value)
            self.regenerate()
        elif name == 'bare':
            if '@' in value:
                u, d = value.split('@', 1)
                object.__setattr__(self, "_user", u)
                object.__setattr__(self, "_domain", d)
            else:
                object.__setattr__(self, "_user", '')
                object.__setattr__(self, "_domain", value)
            self.regenerate()
        else:
            object.__setattr__(self, name, value)

    def regenerate(self):
        """Generate a new JID based on current values, useful after editing."""
        jid = ""
        if self.user:
            jid = "%s@" % self.user
        jid += self.domain
        if self.resource:
            jid += "/%s" % self.resource
        self.reset(jid)

    def __str__(self):
        """Use the full JID as the string value."""
        return self.full
