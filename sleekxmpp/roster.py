"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging


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
        xmpp -- The main SleekXMPP instance.
        db   -- Optional interface object to an external datastore.

    Methods:
        add -- Create a new roster node for a JID.
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
        self._rosters = {}

    def __getitem__(self, key):
        """
        Return the roster node for a JID.

        A new roster node will be created if one
        does not already exist.

        Arguments:
            key -- Return the roster for this JID.
        """
        if key not in self._rosters:
            self.add(key, self.db)
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
        if node not in self._rosters:
            self._rosters[node] = RosterNode(self.xmpp, node, self.db)


class RosterNode(object):

    """

    Attributes:
        xmpp           -- The main SleekXMPP instance.
        jid            -- The JID that owns the roster node.
        db             -- Optional interface to an external datastore.
        auto_authorize -- Determines how authorizations are handled:
                            True  -- Accept all subscriptions.
                            False -- Reject all subscriptions.
                            None  -- Subscriptions must be
                                     manually authorized.
                          Defaults to True.
        auto_subscribe -- Determines if bi-directional subscriptions
                          are created after automatically authrorizing
                          a subscription request.
                          Defaults to True

    Methods:
        add         -- Add a JID to the roster.
        update      -- Update a JID's subscription information.
        subscribe   -- Subscribe to a JID.
        unsubscribe -- Unsubscribe from a JID.
        remove      -- Remove a JID from the roster.
        presence    -- Return presence information for a JID's resources.
    """

    def __init__(self, xmpp, jid, db=None):
        """
        Create a roster node for a JID.

        Arguments:
            xmpp -- The main SleekXMPP instance.
            jid  -- The JID that owns the roster.
            db   -- Optional interface to an external datastore.
        """
        self.xmpp = xmpp
        self.jid = jid
        self.db = db
        self.auto_authorize = True
        self.auto_subscribe = True
        self._jids = {}

    def __getitem__(self, key):
        """
        Return the roster item for a subscribed JID.

        A new item entry will be created if one does not already exist.
        """
        if key not in self._jids:
            self.add(key, save=True)
        return self._jids[key]

    def keys(self):
        """Return a list of all subscribed JIDs."""
        return self._jids.keys()

    def __iter__(self):
        """Iterate over the roster items."""
        return self._jids.__iter__()

    def add(self, jid, name='', groups=None, afrom=False, ato=False,
            pending_in=False, pending_out=False, whitelisted=False,
            save=False):
        """
        Add a new roster item entry.

        Arguments:
            jid         -- The JID for the roster item.
            name        -- An alias for the JID.
            groups      -- A list of group names.
            afrom       -- Indicates if the JID has a subscription state
                           of 'from'. Defaults to False.
            ato         -- Indicates if the JID has a subscription state
                           of 'to'. Defaults to False.
            pending_in  -- Indicates if the JID has sent a subscription
                           request to this connection's JID.
                           Defaults to False.
            pending_out -- Indicates if a subscription request has been sent
                           to this JID.
                           Defaults to False.
            whitelisted -- Indicates if a subscription request from this JID
                           should be automatically authorized.
                           Defaults to False.
            save        -- Indicates if the item should be persisted
                           immediately to an external datastore,
                           if one is used.
                           Defaults to False.
        """

        state = {'name': name,
                 'groups': groups or [],
                 'from': afrom,
                 'to': ato,
                 'pending_in': pending_in,
                 'pending_out': pending_out,
                 'whitelisted': whitelisted,
                 'subscription': 'none'}
        self._jids[jid] = RosterItem(self.xmpp, jid, self.jid,
                                     state=state, db=self.db)
        if save:
            self._jids[jid].save()

    def subscribe(self, jid):
        """
        Subscribe to the given JID.

        Arguments:
            jid -- The JID to subscribe to.
        """
        self._jids[jid].subscribe()

    def unsubscribe(self, jid):
        """
        Unsubscribe from the given JID.

        Arguments:
            jid -- The JID to unsubscribe from.
        """
        self._jids[jid].unsubscribe()

    def remove(self, jid):
        """
        Remove a JID from the roster.

        Arguments:
            jid -- The JID to remove.
        """
        self._jids[jid].remove()
        if not self.xmpp.is_component:
            self.update(jid, subscription='remove')

    def update(self, jid, name=None, subscription=None, groups=[]):
        """
        Update a JID's subscription information.

        Arguments:
            jid          -- The JID to update.
            name         -- Optional alias for the JID.
            subscription -- The subscription state. May be one of: 'to',
                            'from', 'both', 'none', or 'remove'.
            groups       -- A list of group names.
        """
        self._jids[jid]['name'] = name
        self._jids[jid]['groups'] = group
        self._jids[jid].save()

        if not self.xmpp.is_component:
            iq = self.Iq()
            iq['type'] = 'set'
            iq['roster']['items'] = {jid: {'name': name,
                                           'subscription': subscription,
                                           'groups': groups}}
            response = iq.send()
            return response and response['type'] == 'result'

    def presence(self, jid, resource=None):
        """
        Retrieve the presence information of a JID.

        May return either all online resources' status, or
        a single resource's status.

        Arguments:
            jid      -- The JID to lookup.
            resource -- Optional resource for returning
                        only the status of a single connection.
        """
        if resource is None:
            return self._jids[jid].resources

        default_presence = {'status': '',
                            'priority': 0,
                            'show': ''}
        return self._jids[jid].resources.get(resource,
                                             default_presence)


class RosterItem(object):

    def __init__(self, xmpp, jid, owner=None,
                 state=None, db=None):
        self.xmpp = xmpp
        self.jid = jid
        self.owner = owner or self.xmpp.jid
        self.last_status = None
        self.resources = {}
        self.db = db
        self._state = state or {
                'from': False,
                'to': False,
                'pending_in': False,
                'pending_out': False,
                'whitelisted': False,
                'subscription': 'none',
                'name': '',
                'groups': []}
        self._db_state = {}
        self.load()

    def load(self):
        if self.db:
            item = self.db.load(self.owner, self.jid,
                                       self._db_state)
            if item:
                self['name'] = item['name']
                self['groups'] = item['groups']
                self['from'] = item['from']
                self['to'] = item['to']
                self['whitelisted'] = item['whitelisted']
                self['pending_out'] = item['pending_out']
                self['pending_in'] = item['pending_in']
                self['subscription'] = self._subscription()
            return self._state
        return None

    def save(self):
        if self.db:
            self.db.save(self.owner, self.jid,
                         self._state, self._db_state)

    def __getitem__(self, key):
        if key in self._state:
            if key == 'subscription':
                return self._subscription()
            return self._state[key]
        else:
            raise KeyError

    def __setitem__(self, key, value):
        print "%s: %s" % (key, value)
        if key in self._state:
            if key in ['name', 'subscription', 'groups']:
                self._state[key] = value
            else:
                value = str(value).lower()
                self._state[key] = value in ('true', '1', 'on', 'yes')
        else:
            raise KeyError

    def _subscription(self):
        if self['to'] and self['from']:
            return 'both'
        elif self['from']:
            return 'from'
        elif self['to']:
            return 'to'
        else:
            return 'none'

    def remove(self):
        """
        Remove the jids subscription, inform it if it is
        subscribed, and unwhitelist it.
        """
        if self['to']:
            p = self.xmpp.Presence()
            p['to'] = self.jid
            p['type'] = ['unsubscribe']
            if self.xmpp.is_component:
                p['from'] = self.owner
            p.send()
            self['to'] = False
        self['whitelisted'] = False
        self.save()

    def subscribe(self):
        p = self.xmpp.Presence()
        p['to'] = self.jid
        p['type'] = 'subscribe'
        if self.xmpp.is_component:
            p['from'] = self.owner
        self['pending_out'] = True
        self.save()
        p.send()

    def authorize(self):
        self['from'] = True
        self['pending_in'] = False
        self.save()
        self._subscribed()
        self.send_last_presence()

    def unauthorize(self):
        self['from'] = False
        self['pending_in'] = False
        self.save()
        self._unsubscribed()
        p = self.xmpp.Presence()
        p['to'] = self.jid
        p['type'] = 'unavailable'
        if self.xmpp.is_component:
            p['from'] = self.owner
        p.send()

    def _subscribed(self):
        p = self.xmpp.Presence()
        p['to'] = self.jid
        p['type'] = 'subscribed'
        if self.xmpp.is_component:
            p['from'] = self.owner
        p.send()

    def unsubscribe(self):
        p = self.xmpp.Presence()
        p['to'] = self.jid
        p['type'] = 'unsubscribe'
        if self.xmpp.is_component:
            p['from'] = self.owner
        self.save()
        p.send()

    def _unsubscribed(self):
        p = self.xmpp.Presence()
        p['to'] = self.jid
        p['type'] = 'unsubscribed'
        if self.xmpp.is_component:
            p['from'] = self.owner
        p.send()

    def send_presence(self, ptype='available', status=None):
        p = self.xmpp.Presence()
        p['to'] = self.jid
        p['type'] = ptype
        p['status'] = status
        if self.xmpp.is_component:
            p['from'] = self.owner
        self.last_status = p
        p.send()

    def send_last_presence(self):
        if self.last_status is None:
            self.send_presence()
        else:
            self.last_status.send()

    def handle_available(self, presence):
        resource = presence['from'].resource
        data = {'status': presence['status'],
                'show': presence['show'],
                'priority': presence['priority']}
        if not self.resources:
            self.xmpp.event('got_online', presence)
        if resource not in self.resources:
            self.resources[resource] = {}
        self.resources[resource].update(data)

    def handle_unavailable(self, presence):
        resource = presence['from'].resource
        if not self.resources:
            return
        if resource in self.resources:
            del self.resources[resource]
        if not self.resources:
            self.xmpp.event('got_offline', presence)

    def handle_subscribe(self, presence):
        """
        +------------------------------------------------------------------+
        |  EXISTING STATE          |  DELIVER?  |  NEW STATE               |
        +------------------------------------------------------------------+
        |  "None"                  |  yes       |  "None + Pending In"     |
        |  "None + Pending Out"    |  yes       |  "None + Pending Out/In" |
        |  "None + Pending In"     |  no        |  no state change         |
        |  "None + Pending Out/In" |  no        |  no state change         |
        |  "To"                    |  yes       |  "To + Pending In"       |
        |  "To + Pending In"       |  no        |  no state change         |
        |  "From"                  |  no *      |  no state change         |
        |  "From + Pending Out"    |  no *      |  no state change         |
        |  "Both"                  |  no *      |  no state change         |
        +------------------------------------------------------------------+
        """
        if not self['from'] and not self['pending_in']:
            self['pending_in'] = True
            self.xmpp.event('roster_subscription_request', presence)
        elif self['from']:
            self._subscribed()
        self.save()

    def handle_subscribed(self, presence):
        """
        +------------------------------------------------------------------+
        |  EXISTING STATE          |  DELIVER?  |  NEW STATE               |
        +------------------------------------------------------------------+
        |  "None"                  |  no        |  no state change         |
        |  "None + Pending Out"    |  yes       |  "To"                    |
        |  "None + Pending In"     |  no        |  no state change         |
        |  "None + Pending Out/In" |  yes       |  "To + Pending In"       |
        |  "To"                    |  no        |  no state change         |
        |  "To + Pending In"       |  no        |  no state change         |
        |  "From"                  |  no        |  no state change         |
        |  "From + Pending Out"    |  yes       |  "Both"                  |
        |  "Both"                  |  no        |  no state change         |
        +------------------------------------------------------------------+
        """
        if not self['to'] and self['pending_out']:
            self['pending_out'] = False
            self['to'] = True
            self.xmpp.event('roster_subscription_authorized', presence)
        self.save()

    def handle_unsubscribe(self, presence):
        """
        +------------------------------------------------------------------+
        |  EXISTING STATE          |  DELIVER?  |  NEW STATE               |
        +------------------------------------------------------------------+
        |  "None"                  |  no        |  no state change         |
        |  "None + Pending Out"    |  no        |  no state change         |
        |  "None + Pending In"     |  yes *     |  "None"                  |
        |  "None + Pending Out/In" |  yes *     |  "None + Pending Out"    |
        |  "To"                    |  no        |  no state change         |
        |  "To + Pending In"       |  yes *     |  "To"                    |
        |  "From"                  |  yes *     |  "None"                  |
        |  "From + Pending Out"    |  yes *     |  "None + Pending Out     |
        |  "Both"                  |  yes *     |  "To"                    |
        +------------------------------------------------------------------+
        """
        if not self['from']  and self['pending_in']:
            self['pending_in'] = False
            self._unsubscribed()
        elif self['from']:
            self['from'] = False
            self._unsubscribed()
            self.xmpp.event('roster_subscription_remove', presence)
        self.save()

    def handle_unsubscribed(self, presence):
        """
        +------------------------------------------------------------------+
        |  EXISTING STATE          |  DELIVER?  |  NEW STATE               |
        +------------------------------------------------------------------+
        |  "None"                  |  no        |  no state change         |
        |  "None + Pending Out"    |  yes       |  "None"                  |
        |  "None + Pending In"     |  no        |  no state change         |
        |  "None + Pending Out/In" |  yes       |  "None + Pending In"     |
        |  "To"                    |  yes       |  "None"                  |
        |  "To + Pending In"       |  yes       |  "None + Pending In"     |
        |  "From"                  |  no        |  no state change         |
        |  "From + Pending Out"    |  yes       |  "From"                  |
        |  "Both"                  |  yes       |  "From"                  |
        +------------------------------------------------------------------
        """
        if not self['to'] and self['pending_out']:
            self['pending_out'] = False
        elif self['to'] and not self['pending_out']:
            self['to'] = False
            self.xmpp.event('roster_subscription_removed', presence)
        self.save()

    def handle_probe(self, presence):
        if self['to']:
            self.send_last_presence()
        if self['pending_out']:
            self.subscribe()
        if not self['to']:
            self._unsubscribed()
