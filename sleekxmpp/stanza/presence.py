"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import Error
from sleekxmpp.stanza.rootstanza import RootStanza
from sleekxmpp.xmlstream import StanzaBase, ET


class Presence(RootStanza):

    """
    XMPP's <presence> stanza allows entities to know the status of other
    clients and components. Since it is currently the only multi-cast
    stanza in XMPP, many extensions add more information to <presence>
    stanzas to broadcast to every entry in the roster, such as
    capabilities, music choices, or locations (XEP-0115: Entity Capabilities
    and XEP-0163: Personal Eventing Protocol).

    Since <presence> stanzas are broadcast when an XMPP entity changes
    its status, the bulk of the traffic in an XMPP network will be from
    <presence> stanzas. Therefore, do not include more information than
    necessary in a status message or within a <presence> stanza in order
    to help keep the network running smoothly.

    Example <presence> stanzas:
        <presence />

        <presence from="user@example.com">
          <show>away</show>
          <status>Getting lunch.</status>
          <priority>5</priority>
        </presence>

        <presence type="unavailable" />

        <presence to="user@otherhost.com" type="subscribe" />

    Stanza Interface:
        priority -- A value used by servers to determine message routing.
        show     -- The type of status, such as away or available for chat.
        status   -- Custom, human readable status message.

    Attributes:
        types     -- One of: available, unavailable, error, probe,
                         subscribe, subscribed, unsubscribe,
                         and unsubscribed.
        showtypes -- One of: away, chat, dnd, and xa.

    Methods:
        setup        -- Overrides StanzaBase.setup
        reply        -- Overrides StanzaBase.reply
        set_show     -- Set the value of the <show> element.
        get_type     -- Get the value of the type attribute or <show> element.
        set_type     -- Set the value of the type attribute or <show> element.
        get_priority -- Get the value of the <priority> element.
        set_priority -- Set the value of the <priority> element.
    """

    namespace = 'jabber:client'
    name = 'presence'
    interfaces = set(('type', 'to', 'from', 'id', 'show',
                      'status', 'priority'))
    sub_interfaces = set(('show', 'status', 'priority'))
    plugin_attrib = name

    types = set(('available', 'unavailable', 'error', 'probe', 'subscribe',
                 'subscribed', 'unsubscribe', 'unsubscribed'))
    showtypes = set(('dnd', 'chat', 'xa', 'away'))

    def setup(self, xml=None):
        """
        Populate the stanza object using an optional XML object.

        Overrides ElementBase.setup.

        Arguments:
            xml -- Use an existing XML object for the stanza's values.
        """
        # To comply with PEP8, method names now use underscores.
        # Deprecated method names are re-mapped for backwards compatibility.
        self.setShow = self.set_show
        self.getType = self.get_type
        self.setType = self.set_type
        self.delType = self.get_type
        self.getPriority = self.get_priority
        self.setPriority = self.set_priority

        return StanzaBase.setup(self, xml)

    def exception(self, e):
        """
        Override exception passback for presence.
        """
        pass

    def set_show(self, show):
        """
        Set the value of the <show> element.

        Arguments:
            show -- Must be one of: away, chat, dnd, or xa.
        """
        if show is None:
            self._del_sub('show')
        elif show in self.showtypes:
            self._set_sub_text('show', text=show)
        return self

    def get_type(self):
        """
        Return the value of the <presence> stanza's type attribute, or
        the value of the <show> element.
        """
        out = self._get_attr('type')
        if not out:
            out = self['show']
        if not out or out is None:
            out = 'available'
        return out

    def set_type(self, value):
        """
        Set the type attribute's value, and the <show> element
        if applicable.

        Arguments:
            value -- Must be in either self.types or self.showtypes.
        """
        if value in self.types:
            self['show'] = None
            if value == 'available':
                value = ''
            self._set_attr('type', value)
        elif value in self.showtypes:
            self['show'] = value
        return self

    def del_type(self):
        """
        Remove both the type attribute and the <show> element.
        """
        self._del_attr('type')
        self._del_sub('show')

    def set_priority(self, value):
        """
        Set the entity's priority value. Some server use priority to
        determine message routing behavior.

        Bot clients should typically use a priority of 0 if the same
        JID is used elsewhere by a human-interacting client.

        Arguments:
            value -- An integer value greater than or equal to 0.
        """
        self._set_sub_text('priority', text=str(value))

    def get_priority(self):
        """
        Return the value of the <presence> element as an integer.
        """
        p = self._get_sub_text('priority')
        if not p:
            p = 0
        try:
            return int(p)
        except ValueError:
            # The priority is not a number: we consider it 0 as a default
            return 0

    def reply(self):
        """
        Set the appropriate presence reply type.

        Overrides StanzaBase.reply.
        """
        if self['type'] == 'unsubscribe':
            self['type'] = 'unsubscribed'
        elif self['type'] == 'subscribe':
            self['type'] = 'subscribed'
        return StanzaBase.reply(self)
