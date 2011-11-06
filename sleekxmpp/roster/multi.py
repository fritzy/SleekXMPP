"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.xmlstream import JID
from sleekxmpp.roster import RosterNode


class Roster(object):

    """
    SleekXMPP's roster manager.

    The roster is divided into "nodes", where each node is responsible
    for a single JID. While the distinction is not strictly necessary
    for client connections, it is a necessity for components that use
    multiple JIDs.

    Rosters may be stored and persisted in an external datastore. An
    interface object to the datastore that loads and saves roster items may
    be provided. See the documentation for the RosterItem class for the
    methods that the datastore interface object must provide.

    Attributes:
        xmpp           -- The main SleekXMPP instance.
        db             -- Optional interface object to an external datastore.
        auto_authorize -- Default auto_authorize value for new roster nodes.
                          Defaults to True.
        auto_subscribe -- Default auto_subscribe value for new roster nodes.
                          Defaults to True.

    Methods:
        add           -- Create a new roster node for a JID.
        send_presence -- Shortcut for sending a presence stanza.
    """

    def __init__(self, xmpp, db=None):
        """
        Create a new roster.

        Arguments:
            xmpp -- The main SleekXMPP instance.
            db   -- Optional interface object to a datastore.
        """
        self.xmpp = xmpp
        self.db = db
        self._auto_authorize = True
        self._auto_subscribe = True
        self._rosters = {}

        if self.db:
            for node in self.db.entries(None, {}):
                self.add(node)

    def __getitem__(self, key):
        """
        Return the roster node for a JID.

        A new roster node will be created if one
        does not already exist.

        Arguments:
            key -- Return the roster for this JID.
        """
        if isinstance(key, JID):
            key = key.bare
        if key not in self._rosters:
            self.add(key)
            self._rosters[key].auto_authorize = self.auto_authorize
            self._rosters[key].auto_subscribe = self.auto_subscribe
        return self._rosters[key]

    def keys(self):
        """Return the JIDs managed by the roster."""
        return self._rosters.keys()

    def __iter__(self):
        """Iterate over the roster nodes."""
        return self._rosters.__iter__()

    def add(self, node):
        """
        Add a new roster node for the given JID.

        Arguments:
            node -- The JID for the new roster node.
        """
        if isinstance(node, JID):
            node = node.bare
        if node not in self._rosters:
            self._rosters[node] = RosterNode(self.xmpp, node, self.db)

    def set_backend(self, db=None):
        """
        Set the datastore interface object for the roster.

        Arguments:
            db -- The new datastore interface.
        """
        self.db = db
        for node in self.db.entries(None, {}):
            self.add(node)
        for node in self._rosters:
            self._rosters[node].set_backend(db)

    def reset(self):
        """
        Reset the state of the roster to forget any current
        presence information. Useful after a disconnection occurs.
        """
        for node in self:
            self[node].reset()

    def send_presence(self, pshow=None, pstatus=None, ppriority=None,
                      pto=None, pfrom=None, ptype=None, pnick=None):
        """
        Create, initialize, and send a Presence stanza.

        Forwards the send request to the appropriate roster to
        perform the actual sending.

        Arguments:
            pshow     -- The presence's show value.
            pstatus   -- The presence's status message.
            ppriority -- This connections' priority.
            pto       -- The recipient of a directed presence.
            ptype     -- The type of presence, such as 'subscribe'.
            pfrom     -- The sender of the presence.
            pnick     -- Optional nickname of the presence's sender.
        """
        self[pfrom].send_presence(ptype=ptype,
                                  pshow=pshow,
                                  pstatus=pstatus,
                                  ppriority=ppriority,
                                  pnick=pnick,
                                  pto=pto)

    @property
    def auto_authorize(self):
        """
        Auto accept or deny subscription requests.

        If True, auto accept subscription requests.
        If False, auto deny subscription requests.
        If None, don't automatically respond.
        """
        return self._auto_authorize

    @auto_authorize.setter
    def auto_authorize(self, value):
        """
        Auto accept or deny subscription requests.

        If True, auto accept subscription requests.
        If False, auto deny subscription requests.
        If None, don't automatically respond.
        """
        self._auto_authorize = value
        for node in self._rosters:
            self._rosters[node].auto_authorize = value

    @property
    def auto_subscribe(self):
        """
        Auto send requests for mutual subscriptions.

        If True, auto send mutual subscription requests.
        """
        return self._auto_subscribe

    @auto_subscribe.setter
    def auto_subscribe(self, value):
        """
        Auto send requests for mutual subscriptions.

        If True, auto send mutual subscription requests.
        """
        self._auto_subscribe = value
        for node in self._rosters:
            self._rosters[node].auto_subscribe = value
